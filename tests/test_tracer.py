def test_tracing_off_by_default_and_decorator_is_noop():
    from weave_integration import tracer

    def fn(x):
        return x

    assert tracer.WANDB_ENABLED is False
    assert tracer.trace_agent("x")(fn) is fn
