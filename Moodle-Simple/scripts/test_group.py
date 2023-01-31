import os
import secrets
import string

import pytest
import yaml
from group import (
    GROUP_VARS_DIR,
    load_group_var,
    load_group_vars,
    remove_group_vars,
    update_group_vars,
)

GROUP_NAME = "group1"
INIT_INT = 7
INIT_STR = "text"
INIT_LIST = [2, 5, 11]
INIT_DICT = {"a": 2, "b": 3}
INIT_PARAMS = {
    "int": INIT_INT,
    "str": INIT_STR,
    "list": INIT_LIST,
    "dict": INIT_DICT,
}
INIT_PARAMS_0 = {
    "int": INIT_INT,
    "str": INIT_STR,
}
INIT_PARAMS_1 = {
    "list": INIT_LIST,
    "dict": INIT_DICT,
}
NEW_INT = 11
NEW_FLOAT = 3.7
NEW_DICT = {"x": 3.4, "z": -1.2}
NEW_PARAMS = {"int": NEW_INT, "float": NEW_FLOAT, "dict": NEW_DICT}
VAULT_PASSWORD = "".join(
    secrets.choice(string.ascii_letters + string.digits + string.punctuation)
    for x in range(10)
)


class TestNoData:
    def test_load_group_vars(self, tmp_path):
        vars = load_group_vars(GROUP_NAME, tmp_path)
        assert vars == {}

    def test_load_group_var(self, tmp_path):
        with pytest.raises(KeyError):
            load_group_var(GROUP_NAME, "int", tmp_path)

    def test_update_group_vars(self, tmp_path):
        update_group_vars(GROUP_NAME, work_dir=tmp_path, **NEW_PARAMS)
        vars = load_group_vars(GROUP_NAME, tmp_path)
        assert len(vars) == 3
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["dict"] == NEW_DICT

    def test_update_group_vars_with_filename(self, tmp_path):
        update_group_vars(
            GROUP_NAME, _file="01-params", work_dir=tmp_path, **NEW_PARAMS
        )
        vars = load_group_vars(GROUP_NAME, tmp_path)
        assert len(vars) == 3
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["dict"] == NEW_DICT
        assert (tmp_path / GROUP_VARS_DIR / GROUP_NAME / "01-params").exists()

    def test_remove_group_vars(self, tmp_path):
        remove_group_vars(GROUP_NAME, *NEW_PARAMS.keys(), work_dir=tmp_path)
        vars = load_group_vars(GROUP_NAME, tmp_path)
        assert len(vars) == 0


class TestSingleFile:
    def test_load_group_vars(self, group_vars):
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert vars == INIT_PARAMS

    @pytest.mark.parametrize(["key", "expected"], INIT_PARAMS.items())
    def test_load_group_var(self, group_vars, key, expected):
        value = load_group_var(GROUP_NAME, key, group_vars)
        assert value == expected

    def test_update_group_vars(self, group_vars):
        update_group_vars(GROUP_NAME, work_dir=group_vars, **NEW_PARAMS)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 5
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["dict"] == NEW_DICT

    def test_remove_group_vars(self, group_vars):
        remove_group_vars(GROUP_NAME, *NEW_PARAMS.keys(), work_dir=group_vars)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 2
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST

    @pytest.fixture
    def group_vars(self, tmp_path):
        vars_path = tmp_path / GROUP_VARS_DIR / f"{GROUP_NAME}.yml"
        vars_path.parent.mkdir(parents=True, exist_ok=True)
        with vars_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS, f)
        yield tmp_path
        for x in vars_path.parent.glob("*"):
            x.unlink()
        vars_path.parent.rmdir()


class TestSubDirectory:
    def test_load_group_vars(self, group_vars):
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert vars == INIT_PARAMS

    @pytest.mark.parametrize(["key", "expected"], INIT_PARAMS.items())
    def test_load_group_var(self, group_vars, key, expected):
        value = load_group_var(GROUP_NAME, key, group_vars)
        assert value == expected

    def test_update_group_vars(self, group_vars):
        update_group_vars(GROUP_NAME, work_dir=group_vars, **NEW_PARAMS)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 5
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["dict"] == NEW_DICT

    def test_remove_group_vars(self, group_vars):
        remove_group_vars(GROUP_NAME, *NEW_PARAMS.keys(), work_dir=group_vars)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 2
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST

    @pytest.fixture
    def group_vars(self, tmp_path):
        vars_path = tmp_path / GROUP_VARS_DIR / GROUP_NAME / "params.yml"
        vars_path.parent.mkdir(parents=True, exist_ok=True)
        with vars_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS, f)
        yield tmp_path
        for x in vars_path.parent.glob("*"):
            x.unlink()
        vars_path.parent.rmdir()


class TestMultiFiles:
    def test_load_group_vars(self, group_vars):
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert vars == INIT_PARAMS

    @pytest.mark.parametrize(["key", "expected"], INIT_PARAMS.items())
    def test_load_group_var(self, group_vars, key, expected):
        value = load_group_var(GROUP_NAME, key, group_vars)
        assert value == expected

    def test_update_group_vars(self, group_vars):
        update_group_vars(GROUP_NAME, work_dir=group_vars, **NEW_PARAMS)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 5
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["dict"] == NEW_DICT

    def test_update_group_vars_with_filename(self, group_vars):
        update_group_vars(
            GROUP_NAME, _file="20-params", work_dir=group_vars, **NEW_PARAMS
        )
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 5
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["dict"] == NEW_DICT
        assert (group_vars / GROUP_VARS_DIR / GROUP_NAME / "20-params").exists()

    def test_update_group_vars_with_filename2(self, group_vars):
        # ファイル名を指定してgroup_varsの更新を行うと後から読み込まれるファイルに記述されている変数を更新しない
        update_group_vars(
            GROUP_NAME, _file="00-params", work_dir=group_vars, **NEW_PARAMS
        )
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 5
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["dict"] == INIT_DICT

    def test_remove_group_vars(self, group_vars):
        remove_group_vars(GROUP_NAME, *NEW_PARAMS.keys(), work_dir=group_vars)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 2
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST

    @pytest.fixture
    def group_vars(self, tmp_path):
        vars0_path = tmp_path / GROUP_VARS_DIR / GROUP_NAME / "00-params.yml"
        vars0_path.parent.mkdir(parents=True, exist_ok=True)
        with vars0_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS_0, f)
        vars1_path = tmp_path / GROUP_VARS_DIR / GROUP_NAME / "01-params.yml"
        with vars1_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS_1, f)
        yield tmp_path
        for x in vars0_path.parent.glob("*"):
            x.unlink()
        vars0_path.parent.rmdir()


class TestDupFiles:
    def test_load_group_vars(self, group_vars):
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert vars == INIT_PARAMS

    @pytest.mark.parametrize(["key", "expected"], INIT_PARAMS.items())
    def test_load_group_var(self, group_vars, key, expected):
        value = load_group_var(GROUP_NAME, key, group_vars)
        assert value == expected

    def test_update_group_vars(self, group_vars):
        update_group_vars(GROUP_NAME, work_dir=group_vars, **NEW_PARAMS)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 5
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["dict"] == NEW_DICT

    def test_remove_group_vars(self, group_vars):
        remove_group_vars(GROUP_NAME, *NEW_PARAMS.keys(), work_dir=group_vars)
        vars = load_group_vars(GROUP_NAME, group_vars)
        assert len(vars) == 2
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST

    @pytest.fixture
    def group_vars(self, tmp_path):
        vars0_path = tmp_path / GROUP_VARS_DIR / GROUP_NAME / "00-params.yml"
        vars0_path.parent.mkdir(parents=True, exist_ok=True)
        with vars0_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS, f)
        vars1_path = tmp_path / GROUP_VARS_DIR / GROUP_NAME / "01-params.yml"
        with vars1_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS, f)
        yield tmp_path
        for x in vars0_path.parent.glob("*"):
            x.unlink()
        vars0_path.parent.rmdir()


class TestEncrypt:
    def test_encrypt(self, group_vars):
        update_group_vars(GROUP_NAME, _encrypt=True, work_dir=group_vars, **NEW_PARAMS)
        vars = load_group_vars(GROUP_NAME, work_dir=group_vars, _decrypt=True)
        assert len(vars) == 5
        assert vars["str"] == INIT_STR
        assert vars["list"] == INIT_LIST
        assert vars["int"] == NEW_INT
        assert vars["float"] == NEW_FLOAT
        assert vars["dict"] == NEW_DICT

    @pytest.fixture
    def group_vars(self, tmp_path):
        vars_path = tmp_path / GROUP_VARS_DIR / GROUP_NAME / "params.yml"
        vars_path.parent.mkdir(parents=True, exist_ok=True)
        with vars_path.open(mode="w") as f:
            yaml.safe_dump(INIT_PARAMS, f)
        password_file = tmp_path / ".password"
        with password_file.open(mode="w") as f:
            f.write(VAULT_PASSWORD)
        os.environ["ANSIBLE_VAULT_PASSWORD_FILE"] = str(password_file.resolve())
        yield tmp_path
        for x in vars_path.parent.glob("*"):
            x.unlink()
        vars_path.parent.rmdir()
