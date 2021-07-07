import warnings
from pathlib import Path
from typing import List, Optional

import typer

from bioimageio.spec import commands

app = typer.Typer()  # https://typer.tiangolo.com/


@app.command()
def package(
    rdf_source: str = typer.Argument(..., help="RDF source as relative file path or URI"),
    path: Path = typer.Argument(Path() / "{src_name}-package.zip", help="Save package as"),
    update_format: bool = typer.Option(
        False,
        help="Update format version to the latest version (might fail even if source adheres to an old format version). "
        "To inform the format update the source may specify fields of future versions in "
        "config:future:<future version>.",  # todo: add future documentation
    ),
    weights_priority_order: Optional[List[str]] = typer.Option(
        None,
        "-wpo",
        help="For model packages only. "
        "If given only the first weights matching the given weight formats are included. "
        "Defaults to include all weights present in source.",
        show_default=False,
    ),
) -> int:
    return commands.package(rdf_source, path, update_format, weights_priority_order)


package.__doc__ = commands.package.__doc__


@app.command()
def validate(
    rdf_source: str = typer.Argument(..., help="RDF source as relative file path or URI"),
    update_format: bool = typer.Option(
        False,
        help="Update format version to the latest (might fail even if source adheres to an old format version). "
        "To inform the format update the source may specify fields of future versions in "
        "config:future:<future version>.",  # todo: add future documentation
    ),
    update_format_inner: bool = typer.Option(
        None, help="For collection RDFs only. Defaults to value of 'update-format'."
    ),
) -> int:
    return commands.validate(rdf_source, update_format, update_format_inner)


validate.__doc__ = commands.validate.__doc__


@app.command()
def verify_spec(model_yaml: str, auto_convert: bool = False):
    """'verify-spec' is deprecated in favor of 'validate'"""
    warnings.warn("'verify_spec' is deprecated in favor of 'validate'")
    return validate(model_yaml, auto_convert)


@app.command()
def verify_bioimageio_manifest(manifest_yaml: Path, auto_convert: bool = False):
    """'verify-bioimageio-manifest' is deprecated in favor of 'validate'"""
    warnings.warn("'verify_bioimageio_manifest' is deprecated in favor of 'validate'")
    return validate(manifest_yaml.absolute().as_uri(), auto_convert)


if __name__ == "__main__":
    app()
