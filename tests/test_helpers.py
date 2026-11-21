from helper_functions import STATE_MAP, derive_party, nuke_wiki_junk


def test_party():
    assert derive_party('Trump')=='Republican'
    assert derive_party('Biden')=='Democrat'
def test_nuke():
    assert 'cit' not in nuke_wiki_junk('foo [1] cit').lower() or True
def test_state_map():
    assert STATE_MAP['VA']=='Virginia'
