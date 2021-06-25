import os
import re
import sys
from argparse import ArgumentParser
from pathlib import Path

_script_path = Path(__file__).parent

autogen_header = "# Auto-generated by generate_passthrough_modules.py - do not modify\n\n"
autogen_text = autogen_header + "from .{spec_version}.{stem} import *\n"

version_module_pattern = "v(?P<major>\d+)_(?P<minor>\d+)"


def get_config(args):
    return {
        "main_module_path": (_script_path.parent / "bioimageio" / "spec").resolve(),
        "versioned_module_path": (_script_path.parent / "bioimageio" / "spec" / args.target_version).resolve(),
        "target_version": args.target_version,
    }


def remove_autogen_mods(config):
    for f in config["main_module_path"].glob("*.py"):
        mod_txt = f.read_text()
        m = re.match(autogen_header + f"from \.{version_module_pattern}\.", mod_txt)
        if m:
            print(f"Deleting {f} (linked version {m.groupdict()['version']})")
            f.unlink()


def updated_init_content(config) -> str:
    restr = "# autogen: start\n.*# autogen: stop"

    init_file = config["main_module_path"] / "__init__.py"
    assert init_file.exists()
    versioned_init = config["versioned_module_path"] / "__init__.py"
    module_init = config["main_module_path"] / "__init__.py"
    vx_init = module_init.read_text()
    if not re.findall(restr, vx_init, flags=re.DOTALL):
        raise RuntimeError(
            f"Could not find autogen markers in {module_init}. Excpected to find\n\n# autogen: start\n...\n# autogen: stop\n\nin your __init__."
        )
    return re.sub(restr, f"# autogen: start\n{versioned_init.read_text()}\n# autogen: stop", vx_init, flags=re.DOTALL)


def update_init(config):
    module_init = config["main_module_path"] / "__init__.py"
    module_init.write_text(updated_init_content(config))


def add_autogen_mods(config):
    for f in config["versioned_module_path"].glob("*.py"):
        if f.name.startswith("__"):
            continue

        tmp = config["main_module_path"] / f.name
        tmp.write_text(autogen_text.format(spec_version=config["target_version"], stem=f.stem))


def is_valid_generated_module(module_file: Path, spec_version: str):
    module_txt = module_file.read_text()
    if module_txt == autogen_text.format(spec_version=spec_version, stem=module_file.stem):
        return True

    return False


def check_main(args) -> int:
    print(f"Checking `bioimageio.spec` modules to link against {args.target_version}.")
    config = get_config(args)
    print(
        f"Assuming module location {config['main_module_path']}, with target spec in {config['versioned_module_path']}."
    )

    ret = 0
    for f in config["versioned_module_path"].glob("*.py"):
        if f.name == "__init__.py":
            continue
        if not (config["main_module_path"] / f.name).exists() or not is_valid_generated_module(
            config["main_module_path"] / f.name, config["target_version"]
        ):
            ret += 1
            print(f"Could not find {config['main_module_path'] / f.name}")

    if ret == 0:
        print("All seems fine.")
    else:
        print("Issues found, try regenerating.")
    return ret


def generate_main(args) -> int:
    print(f"Generating `bioimageio.spec` modules to link against {args.target_version}.")

    config = get_config(args)
    remove_autogen_mods(config)
    add_autogen_mods(config)
    update_init(config)

    return 0


def parse_args():
    p = ArgumentParser(
        description=(
            "script that generates Python module files in bioimageio.spec that "
            "'link' to a certain spec version. The generated modules act as pass"
            "-through, via `from .vX_Y import *"
        )
    )
    p.add_argument("command", choices=["check", "generate"])
    p.add_argument(
        "--target-version",
        default="latest",
        help=(
            "Name of the version submodule. This submodule will be made available in `bioimageio.spec`. Example 'v0_3'."
        ),
        type=str,
    )

    args = p.parse_args()
    return args


def get_ordered_version_submodules():
    matches = [
        re.fullmatch(version_module_pattern, f.name)
        for f in os.scandir(_script_path.parent / "bioimageio" / "spec")
        if f.is_dir()
    ]
    matches = sorted(filter(None, matches), key=lambda m: (m["major"], m["minor"]))
    return [m.string for m in matches]


def resolve_latest_target_version(args):
    if args.target_version == "latest":
        args.target_version = get_ordered_version_submodules()[-1]

    return args


def main():
    args = parse_args()
    args = resolve_latest_target_version(args)
    if args.command == "check":
        return check_main(args)
    elif args.command == "generate":
        return check_main(args)
    else:
        raise NotImplementedError(args.command)


if __name__ == "__main__":
    sys.exit(main())
