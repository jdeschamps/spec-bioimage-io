import os
import pathlib
import re
import traceback
import zipfile
from io import BytesIO, StringIO
from typing import Dict, IO, List, Sequence, Union
from urllib.request import urlopen

from marshmallow import ValidationError

from .io_ import load_raw_resource_description
from .shared.common import DOI_REGEX, yaml


def validate(
    rdf_source: Union[dict, os.PathLike, IO, str, bytes],
    update_format: bool = False,
    update_format_inner: bool = None,
    verbose: bool = False,
) -> Dict[str, Union[str, list, dict]]:
    """Validate a BioImage.IO Resource Description File (RDF)."""
    if update_format_inner is None:
        update_format_inner = update_format

    if isinstance(rdf_source, (BytesIO, StringIO)):
        rdf_source = rdf_source.read()
    elif isinstance(rdf_source, os.PathLike):
        # zipfile.is_zipfile cannot deal with all os.PathLike objects (e.g. pytest's `LocalPath`),
        # so we cast to pathlib.Path
        rdf_source = pathlib.Path(rdf_source)

    source_name = str(
        rdf_source.get("name")
        if isinstance(rdf_source, dict)
        else rdf_source[:120]
        if isinstance(rdf_source, (str, bytes))
        else rdf_source
    )

    if not isinstance(rdf_source, dict):
        if isinstance(rdf_source, str):
            if re.fullmatch(DOI_REGEX, rdf_source):  # turn doi into url
                zenodo_sandbox_prefix = "10.5072/zenodo."
                if rdf_source.startswith(zenodo_sandbox_prefix):
                    # zenodo sandbox doi (which is not a valid doi)
                    rdf_source = (
                        f"https://sandbox.zenodo.org/record/{rdf_source[len(zenodo_sandbox_prefix):]}/files/rdf.yaml"
                    )
                else:
                    # resolve doi
                    # todo: make sure the resolved url points to a rdf.yaml or a zipped package
                    rdf_source = urlopen(f"https://doi.org/{rdf_source}?type=URL").url

            if rdf_source.startswith("http"):
                from urllib.request import urlretrieve

                rdf_source, response = urlretrieve(rdf_source)
                # todo: check http response code

            try:
                is_path = pathlib.Path(rdf_source).exists()
            except OSError:
                is_path = False

            if is_path:
                rdf_source = pathlib.Path(rdf_source)

        if yaml is None:
            raise RuntimeError("Cannot validate from file or yaml string without ruamel.yaml dependency!")

        if isinstance(rdf_source, bytes):
            potential_package: Union[pathlib.Path, IO, str] = BytesIO(rdf_source)
            potential_package.seek(0)  # type: ignore
        else:
            potential_package = rdf_source

        if zipfile.is_zipfile(potential_package):
            with zipfile.ZipFile(potential_package) as zf:
                if "rdf.yaml" not in zf.namelist():
                    raise ValueError(f"package {source_name} does not contain 'rdf.yaml'")

                rdf_source = BytesIO(zf.read("rdf.yaml"))

        rdf_source = yaml.load(rdf_source)

    assert isinstance(rdf_source, dict)
    try:
        raw_rd = load_raw_resource_description(rdf_source, update_to_current_format=update_format)
    except ValidationError as e:
        return {source_name: e.normalized_messages()}
    except Exception as e:
        if verbose:
            msg: Union[str, Dict[str, Union[str, Sequence[str]]]] = {
                "error": str(e),
                "traceback": traceback.format_tb(e.__traceback__),
            }
        else:
            msg = str(e)

        return {source_name: msg}

    collection_errors: List[Union[str, dict]] = []
    if raw_rd.type == "collection":
        for inner_category in ["application", "collection", "dataset", "model", "notebook"]:
            for inner in getattr(raw_rd, inner_category) or []:
                try:
                    inner_source = inner.source
                except Exception as e:
                    collection_errors.append(str(e))
                else:
                    inner_errors = validate(inner_source, update_format_inner, update_format_inner, verbose)
                    if inner_errors:
                        collection_errors.append(inner_errors)

    if collection_errors:
        return {source_name: collection_errors}
    else:
        return {}
