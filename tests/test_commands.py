import zipfile
from copy import copy
from io import BytesIO, StringIO

from bioimageio.spec import load_raw_resource_description
from bioimageio.spec.model import format_version, raw_nodes
from bioimageio.spec.shared import yaml


def test_validate_dataset(dataset_rdf):
    from bioimageio.spec.commands import validate

    summary = validate(dataset_rdf, update_format=True, update_format_inner=False)
    assert summary["status"] == "passed", summary
    summary = validate(dataset_rdf, update_format=False, update_format_inner=False)
    assert summary["status"] == "passed", summary


def test_validate_model_as_dict(unet2d_nuclei_broad_any):
    from bioimageio.spec.commands import validate

    assert not validate(unet2d_nuclei_broad_any, update_format=True, update_format_inner=False)["error"]
    assert not validate(unet2d_nuclei_broad_any, update_format=False, update_format_inner=False)["error"]


def test_validate_model_as_url():
    from bioimageio.spec.commands import validate

    assert not validate(
        "https://raw.githubusercontent.com/bioimage-io/spec-bioimage-io/main/example_specs/models/unet2d_nuclei_broad/rdf.yaml",
        update_format=True,
        update_format_inner=False,
    )["error"]
    assert not validate(
        "https://raw.githubusercontent.com/bioimage-io/spec-bioimage-io/main/example_specs/models/unet2d_nuclei_broad/rdf.yaml",
        update_format=False,
        update_format_inner=False,
    )["error"]


def test_validate_model_as_zenodo_sandbox_doi():
    from bioimageio.spec.commands import validate

    doi = "10.5281/zenodo.5744489"
    assert not validate(doi, update_format=False, update_format_inner=False)["error"]


def test_validate_model_as_zenodo_doi():
    from bioimageio.spec.commands import validate

    doi = "10.5281/zenodo.5744490"
    assert not validate(doi, update_format=False, update_format_inner=False)["error"]

    # expecting UnconvertibleError due to missing sha256
    assert validate(doi, update_format=True, update_format_inner=False)["error"]


def test_validate_model_as_bioimageio_full_version_id_partner():
    from bioimageio.spec.commands import validate

    full_version_id = "ilastik/isbi2012_neuron_segmentation_challenge/latest"
    summary = validate(full_version_id, update_format=False, update_format_inner=False)
    assert summary["status"] == "passed", summary["error"]


def test_validate_model_as_bioimageio_full_version_id_zenodo():
    from bioimageio.spec.commands import validate

    full_version_id = "10.5281/zenodo.5874741/5874742"
    summary = validate(full_version_id, update_format=False, update_format_inner=False)
    assert summary["status"] == "passed", summary["error"]


def test_validate_model_as_bioimageio_resource_id_partner():
    from bioimageio.spec.commands import validate

    resource_id = "ilastik/isbi2012_neuron_segmentation_challenge"
    summary = validate(resource_id, update_format=False, update_format_inner=False)
    assert summary["status"] == "passed", summary["error"]


def test_validate_model_as_bioimageio_resource_id_zenodo():
    from bioimageio.spec.commands import validate

    resource_id = "10.5281/zenodo.5874741"
    summary = validate(resource_id, update_format=False, update_format_inner=False)
    assert summary["status"] == "passed", summary["error"]


def test_validate_model_as_bytes_io(unet2d_nuclei_broad_latest_path):
    from bioimageio.spec.commands import validate

    data = BytesIO(unet2d_nuclei_broad_latest_path.read_bytes())
    data.seek(0)
    assert not validate(data, update_format=True, update_format_inner=False)["error"]
    data.seek(0)
    assert not validate(data, update_format=False, update_format_inner=False)["error"]


def test_validate_model_as_string_io(unet2d_nuclei_broad_latest_path):
    from bioimageio.spec.commands import validate

    data = StringIO(unet2d_nuclei_broad_latest_path.read_text())
    data.seek(0)
    assert not validate(data, update_format=True, update_format_inner=False)["error"]
    data.seek(0)
    assert not validate(data, update_format=False, update_format_inner=False)["error"]


def test_validate_model_as_bytes(unet2d_nuclei_broad_latest_path):
    from bioimageio.spec.commands import validate

    data = unet2d_nuclei_broad_latest_path.read_bytes()
    assert not validate(data, update_format=True, update_format_inner=False)["error"]
    assert not validate(data, update_format=False, update_format_inner=False)["error"]


def test_validate_model_as_string(unet2d_nuclei_broad_latest_path):
    from bioimageio.spec.commands import validate

    data = unet2d_nuclei_broad_latest_path.read_text()
    assert not validate(data, update_format=True, update_format_inner=False)["error"]
    assert not validate(data, update_format=False, update_format_inner=False)["error"]


def test_validate_model_package_as_bytes(unet2d_nuclei_broad_latest_path):
    from bioimageio.spec.commands import validate

    data = BytesIO()
    with zipfile.ZipFile(data, "w") as zf:
        zf.write(unet2d_nuclei_broad_latest_path, "rdf.yaml")

    data.seek(0)
    assert not validate(data, update_format=True, update_format_inner=False)["error"]
    data.seek(0)
    assert not validate(data, update_format=False, update_format_inner=False)["error"]


def test_validate_model_package_on_disk(unet2d_nuclei_broad_latest_path, tmpdir):
    from bioimageio.spec.commands import validate

    zf_path = tmpdir / "package.zip"
    with zipfile.ZipFile(zf_path, "w") as zf:
        zf.write(unet2d_nuclei_broad_latest_path, "rdf.yaml")

    assert not validate(zf_path, update_format=True, update_format_inner=False)["error"]
    assert not validate(zf_path, update_format=False, update_format_inner=False)["error"]


def test_validate_invalid_model(unet2d_nuclei_broad_latest):
    from bioimageio.spec.commands import validate

    data = copy(unet2d_nuclei_broad_latest)
    del data["test_inputs"]  # invalidate data
    assert validate(data, update_format=True, update_format_inner=False)["error"]
    assert validate(data, update_format=False, update_format_inner=False)["error"]


def test_validate_generates_warnings(unet2d_nuclei_broad_latest):
    from bioimageio.spec.commands import validate

    data = copy(unet2d_nuclei_broad_latest)
    data["license"] = "BSD-2-Clause-FreeBSD"
    data["run_mode"] = {"name": "fancy"}
    summary = validate(data, update_format=True, update_format_inner=False)

    assert summary["warnings"]


def test_update_format(unet2d_nuclei_broad_before_latest, tmp_path):
    from bioimageio.spec.commands import update_format

    path = tmp_path / "rdf_new.yaml"
    update_format(unet2d_nuclei_broad_before_latest, path)

    assert path.exists()
    model = load_raw_resource_description(path)
    assert model.format_version == format_version


def test_update_rdf_using_paths(unet2d_nuclei_broad_base_path, tmp_path):
    from bioimageio.spec.commands import update_rdf

    in_path = unet2d_nuclei_broad_base_path / "rdf.yaml"
    assert in_path.exists()
    update_path = tmp_path / "update.yaml"
    yaml.dump(dict(name="updated", outputs=[{"name": "updated", "halo": ["KEEP", "DROP", 0, 9, 9]}]), update_path)
    out_path = tmp_path / "output.yaml"
    update_rdf(in_path, update_path, out_path)
    actual = yaml.load(out_path)
    assert actual["name"] == "updated"
    assert actual["outputs"][0]["name"] == "updated"
    assert actual["outputs"][0]["halo"] == [0, 0, 9, 9]


def test_update_rdf_using_dicts(unet2d_nuclei_broad_latest):
    from bioimageio.spec.commands import update_rdf

    source = unet2d_nuclei_broad_latest
    update = dict(name="updated", outputs=[{"name": "updated", "halo": ["KEEP", "DROP", 0, 9, 9]}])
    actual = update_rdf(source, update)
    assert actual["name"] == "updated"
    assert actual["outputs"][0]["name"] == "updated"
    assert actual["outputs"][0]["halo"] == [0, 0, 9, 9]


def test_update_rdf_using_dicts_in_place(unet2d_nuclei_broad_latest):
    from bioimageio.spec.commands import update_rdf

    source = unet2d_nuclei_broad_latest
    update = dict(name="updated", outputs=[{"name": "updated", "halo": ["KEEP", "DROP", 0, 9, 9]}])
    update_rdf(source, update, output=source)
    actual = source
    assert actual["name"] == "updated"
    assert actual["outputs"][0]["name"] == "updated"
    assert actual["outputs"][0]["halo"] == [0, 0, 9, 9]


def test_update_rdf_using_rd(unet2d_nuclei_broad_latest):
    from bioimageio.spec.commands import update_rdf

    source = load_raw_resource_description(unet2d_nuclei_broad_latest)
    update = dict(name="updated", outputs=[{"name": "updated", "halo": ["KEEP", "DROP", 0, 9, 9]}])
    actual = update_rdf(source, update)
    assert isinstance(actual, raw_nodes.Model)
    assert actual.name == "updated"
    assert actual.outputs[0].name == "updated"
    assert actual.outputs[0].halo == [0, 0, 9, 9]
