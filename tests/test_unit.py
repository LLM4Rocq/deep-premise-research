from src.parser.tiny_rocq_parser import TinyRocqParser, Source, Element, Range, Position


"""
WIP
"""

def test__extract_proof_steps():
    parser = TinyRocqParser("8765")
    start_pos = Position(line=1, character=0)
    end_pos = Position(line=1, character=66)
    content_lines = [
        "",
        "Lemma cmp0 x : unify_itv i (Itv.Real `]-oo, +oo[) -> 0 >=< x%:num. Proof. by case: i x => [//| i' [x /=/andP[]]].\n- by case: y => [y /=/andP[]]. Qed.",
    ]
    thm = Element(origin="", name="", statement="", range=Range(start_pos, end_pos))
    source = Source(path="", content="", content_lines=content_lines)
    assert parser._extract_proof_steps(thm, source) == ['Proof.', "by case: i x => [//| i' [x /=/andP[]]].", "-",  "by case: y => [y /=/andP[]].", 'Qed.']

if __name__ == '__main__':
    test__extract_proof_steps()