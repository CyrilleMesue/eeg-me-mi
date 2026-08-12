from eeg_me_mi.config import load_config


def test_toy_config_loads():
    config = load_config("configs/toy.yaml")
    assert config.subjects == (1, 2, 3, 4, 5, 6, 7, 8)
    assert config.runs == tuple(range(3, 15))
    assert config.path("output_root").name == "toy"
    assert config.statistics["bootstrap_replicates"] == 50
    assert config.logistic_c_grid == (0.01, 0.1, 1.0, 10.0)


def test_full_subject_range_is_inclusive():
    config = load_config("configs/truba_full.yaml")
    assert config.subjects[0] == 1
    assert config.subjects[-1] == 109
    assert len(config.subjects) == 109
