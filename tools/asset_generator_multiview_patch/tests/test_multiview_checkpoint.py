from backends.trellis import checkpoint


def test_resume_reuses_only_the_exact_native_mesh_masks_and_inputs(tmp_path):
    ref=tmp_path/'front.png';ref.write_bytes(b'reference pixels')
    out=tmp_path/'generated';out.mkdir()
    (out/'source.glb').write_bytes(b'retained native mesh')
    (out/'generation.json').write_text('{}')
    (out/'foreground_00.png').write_bytes(b'retained alpha mask')
    settings={'generation_seed':42,'trellis_steps':25,'reference_view_angles':['front']}
    identity=checkpoint.signature([ref],settings)
    checkpoint.save(out,identity)
    assert checkpoint.matches(out,identity)
    assert not checkpoint.matches(out,checkpoint.signature([ref],{**settings,'trellis_steps':12}))
    # Post-processing can update its report without discarding the native mesh.
    (out/'generation.json').write_text('{"projection":"failed"}')
    assert checkpoint.matches(out,identity)
    (out/'foreground_00.png').write_bytes(b'changed mask')
    assert not checkpoint.matches(out,identity)
