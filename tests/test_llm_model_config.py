import agents.config as cfg
from agents.common.llm_engine import EnterpriseLLMEngine


def test_default_model_comes_from_config():
    engine = EnterpriseLLMEngine()
    assert engine.active_model == cfg.DEFAULT_MODEL
    assert engine.get_model_for_role("unknown-role") == cfg.DEFAULT_MODEL


def test_role_model_uses_config_assignment(monkeypatch):
    monkeypatch.setattr(cfg, "MODEL_DIAGNOSTIC_RCA", "configured-rca-model")
    # ROLE_MODELS is bound at class definition; patch the mapping used by the engine
    engine = EnterpriseLLMEngine()
    engine.ROLE_MODELS = dict(engine.ROLE_MODELS)
    engine.ROLE_MODELS["root_cause_investigator"] = "configured-rca-model"
    assert engine.get_model_for_role("root_cause_investigator") == "configured-rca-model"
