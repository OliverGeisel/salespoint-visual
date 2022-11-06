from pathlib import Path


def get_configs(directory: Path, max_depth: int = 4) -> list[Path]:
    back = list()
    if directory.is_dir():
        for child in directory.iterdir():
            if child.is_dir() and max_depth:
                back.extend(get_configs(child, max_depth - 1))
            elif child.is_file() and child.suffix == ".config":
                back.append(child)
            else:
                pass
    elif directory.is_file() and directory.suffix == ".config":
        back.append(directory)
    return back


def get_sum_of_config(config: list[str]) -> int:
    sum = 0
    for line in config:
        sum += int(line.split("_")[1])
    return sum


def get_minimal_model(configs: list[Path], diff=0) -> set[str]:
    contents = list()
    features = dict()
    for config in configs:
        with config.open() as config_file:
            content = config_file.readlines()
        print(config_file.name, " ", get_sum_of_config(content))
        contents.append(content)
        for line in content:
            line = line.strip()
            if line in features.keys():
                features[line] += 1
            else:
                features[line] = 1
    num_configs = len(contents)
    back = {k for k, v in features.items() if num_configs - v <= diff}
    return back


class Scenario:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
