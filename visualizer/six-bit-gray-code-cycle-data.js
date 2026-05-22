window.SIX_BIT_GRAY_CODE_CYCLE_DATA = {
  "name": "six_bit_gray_code_single_flip_cycle_invariant",
  "summary": {
    "all_pass": true,
    "state_count": 64,
    "invariant_count": 7,
    "cycle_invariant_row_count": 4,
    "graveyard_variant_count": 3,
    "load_bearing_tool_count": 10,
    "tool_count": 16,
    "visual_payload": "visualizer/six-bit-gray-code-cycle-data.js",
    "scope_note": "Six-bit Gray-code single-flip cycle invariant row. It tests a six-bit, one-line-transition schedule as a comparison surface for heat/work and measurement/feedback cycle grammar. It is symbolic and pre-admission, not QIT runtime promotion."
  },
  "hexagrams": [
    {
      "index": 0,
      "state": 0,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        0,
        0,
        0
      ],
      "lower_trigram": 0,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": null
    },
    {
      "index": 1,
      "state": 1,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        0,
        0,
        0
      ],
      "lower_trigram": 1,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 2,
      "state": 3,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        0,
        0,
        0
      ],
      "lower_trigram": 3,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 3,
      "state": 2,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        0,
        0,
        0
      ],
      "lower_trigram": 2,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 4,
      "state": 6,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        0,
        0,
        0
      ],
      "lower_trigram": 6,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 5,
      "state": 7,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        0,
        0,
        0
      ],
      "lower_trigram": 7,
      "upper_trigram": 0,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 6,
      "state": 5,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        0,
        0,
        0
      ],
      "lower_trigram": 5,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 7,
      "state": 4,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        0,
        0,
        0
      ],
      "lower_trigram": 4,
      "upper_trigram": 0,
      "polarity": "yin_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 8,
      "state": 12,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        1,
        0,
        0
      ],
      "lower_trigram": 4,
      "upper_trigram": 1,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 3
    },
    {
      "index": 9,
      "state": 13,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        1,
        0,
        0
      ],
      "lower_trigram": 5,
      "upper_trigram": 1,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 10,
      "state": 15,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        1,
        0,
        0
      ],
      "lower_trigram": 7,
      "upper_trigram": 1,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 11,
      "state": 14,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        1,
        0,
        0
      ],
      "lower_trigram": 6,
      "upper_trigram": 1,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 12,
      "state": 10,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        1,
        0,
        0
      ],
      "lower_trigram": 2,
      "upper_trigram": 1,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 13,
      "state": 11,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        1,
        0,
        0
      ],
      "lower_trigram": 3,
      "upper_trigram": 1,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 14,
      "state": 9,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        1,
        0,
        0
      ],
      "lower_trigram": 1,
      "upper_trigram": 1,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 15,
      "state": 8,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        1,
        0,
        0
      ],
      "lower_trigram": 0,
      "upper_trigram": 1,
      "polarity": "yin_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 16,
      "state": 24,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        1,
        1,
        0
      ],
      "lower_trigram": 0,
      "upper_trigram": 3,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 4
    },
    {
      "index": 17,
      "state": 25,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        1,
        1,
        0
      ],
      "lower_trigram": 1,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 18,
      "state": 27,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        1,
        1,
        0
      ],
      "lower_trigram": 3,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 19,
      "state": 26,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        1,
        1,
        0
      ],
      "lower_trigram": 2,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 20,
      "state": 30,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        1,
        1,
        0
      ],
      "lower_trigram": 6,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 21,
      "state": 31,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        1,
        1,
        0
      ],
      "lower_trigram": 7,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 22,
      "state": 29,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        1,
        1,
        0
      ],
      "lower_trigram": 5,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 23,
      "state": 28,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        1,
        1,
        0
      ],
      "lower_trigram": 4,
      "upper_trigram": 3,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 24,
      "state": 20,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        0,
        1,
        0
      ],
      "lower_trigram": 4,
      "upper_trigram": 2,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 3
    },
    {
      "index": 25,
      "state": 21,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        0,
        1,
        0
      ],
      "lower_trigram": 5,
      "upper_trigram": 2,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 26,
      "state": 23,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        0,
        1,
        0
      ],
      "lower_trigram": 7,
      "upper_trigram": 2,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 27,
      "state": 22,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        0,
        1,
        0
      ],
      "lower_trigram": 6,
      "upper_trigram": 2,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 28,
      "state": 18,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        0,
        1,
        0
      ],
      "lower_trigram": 2,
      "upper_trigram": 2,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 29,
      "state": 19,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        0,
        1,
        0
      ],
      "lower_trigram": 3,
      "upper_trigram": 2,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 30,
      "state": 17,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        0,
        1,
        0
      ],
      "lower_trigram": 1,
      "upper_trigram": 2,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 31,
      "state": 16,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        0,
        1,
        0
      ],
      "lower_trigram": 0,
      "upper_trigram": 2,
      "polarity": "yin_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 32,
      "state": 48,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        0,
        1,
        1
      ],
      "lower_trigram": 0,
      "upper_trigram": 6,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 5
    },
    {
      "index": 33,
      "state": 49,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        0,
        1,
        1
      ],
      "lower_trigram": 1,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 34,
      "state": 51,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        0,
        1,
        1
      ],
      "lower_trigram": 3,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 35,
      "state": 50,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        0,
        1,
        1
      ],
      "lower_trigram": 2,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 36,
      "state": 54,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        0,
        1,
        1
      ],
      "lower_trigram": 6,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 37,
      "state": 55,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        0,
        1,
        1
      ],
      "lower_trigram": 7,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 38,
      "state": 53,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        0,
        1,
        1
      ],
      "lower_trigram": 5,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 39,
      "state": 52,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        0,
        1,
        1
      ],
      "lower_trigram": 4,
      "upper_trigram": 6,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 40,
      "state": 60,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        1,
        1,
        1
      ],
      "lower_trigram": 4,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 3
    },
    {
      "index": 41,
      "state": 61,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        1,
        1,
        1
      ],
      "lower_trigram": 5,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 42,
      "state": 63,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        1,
        1,
        1
      ],
      "lower_trigram": 7,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 43,
      "state": 62,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        1,
        1,
        1
      ],
      "lower_trigram": 6,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 44,
      "state": 58,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        1,
        1,
        1
      ],
      "lower_trigram": 2,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 45,
      "state": 59,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        1,
        1,
        1
      ],
      "lower_trigram": 3,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 46,
      "state": 57,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        1,
        1,
        1
      ],
      "lower_trigram": 1,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 47,
      "state": 56,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        1,
        1,
        1
      ],
      "lower_trigram": 0,
      "upper_trigram": 7,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 48,
      "state": 40,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        1,
        0,
        1
      ],
      "lower_trigram": 0,
      "upper_trigram": 5,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 4
    },
    {
      "index": 49,
      "state": 41,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        1,
        0,
        1
      ],
      "lower_trigram": 1,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 50,
      "state": 43,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        1,
        0,
        1
      ],
      "lower_trigram": 3,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 51,
      "state": 42,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        1,
        0,
        1
      ],
      "lower_trigram": 2,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 52,
      "state": 46,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        1,
        0,
        1
      ],
      "lower_trigram": 6,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 53,
      "state": 47,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        1,
        0,
        1
      ],
      "lower_trigram": 7,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 54,
      "state": 45,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        1,
        0,
        1
      ],
      "lower_trigram": 5,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 55,
      "state": 44,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        1,
        0,
        1
      ],
      "lower_trigram": 4,
      "upper_trigram": 5,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 56,
      "state": 36,
      "bits_bottom_to_top": [
        0,
        0,
        1,
        0,
        0,
        1
      ],
      "lower_trigram": 4,
      "upper_trigram": 4,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 3
    },
    {
      "index": 57,
      "state": 37,
      "bits_bottom_to_top": [
        1,
        0,
        1,
        0,
        0,
        1
      ],
      "lower_trigram": 5,
      "upper_trigram": 4,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 58,
      "state": 39,
      "bits_bottom_to_top": [
        1,
        1,
        1,
        0,
        0,
        1
      ],
      "lower_trigram": 7,
      "upper_trigram": 4,
      "polarity": "yang_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 59,
      "state": 38,
      "bits_bottom_to_top": [
        0,
        1,
        1,
        0,
        0,
        1
      ],
      "lower_trigram": 6,
      "upper_trigram": 4,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 60,
      "state": 34,
      "bits_bottom_to_top": [
        0,
        1,
        0,
        0,
        0,
        1
      ],
      "lower_trigram": 2,
      "upper_trigram": 4,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 2
    },
    {
      "index": 61,
      "state": 35,
      "bits_bottom_to_top": [
        1,
        1,
        0,
        0,
        0,
        1
      ],
      "lower_trigram": 3,
      "upper_trigram": 4,
      "polarity": "yang_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    },
    {
      "index": 62,
      "state": 33,
      "bits_bottom_to_top": [
        1,
        0,
        0,
        0,
        0,
        1
      ],
      "lower_trigram": 1,
      "upper_trigram": 4,
      "polarity": "yin_heavy",
      "parity": 0,
      "loop_family": "deductive",
      "changed_line_from_previous": 1
    },
    {
      "index": 63,
      "state": 32,
      "bits_bottom_to_top": [
        0,
        0,
        0,
        0,
        0,
        1
      ],
      "lower_trigram": 0,
      "upper_trigram": 4,
      "polarity": "yin_heavy",
      "parity": 1,
      "loop_family": "inductive",
      "changed_line_from_previous": 0
    }
  ],
  "cycle_step_invariant_map": {
    "boundary": "symbolic_cycle_invariant_map_not_admitted_qit_axis",
    "invariants": {
      "line_count_polarity": {
        "local_name": "polarity_gradient",
        "degree_of_freedom": "yin/yang count and parity over six finite lines",
        "observable": "sum(bits) and parity"
      },
      "lower_three_bit_branch": {
        "local_name": "lower_trigram_branch",
        "degree_of_freedom": "bottom three-line branch",
        "observable": "lower_trigram"
      },
      "upper_three_bit_frame": {
        "local_name": "upper_trigram_frame",
        "degree_of_freedom": "top three-line branch/frame",
        "observable": "upper_trigram"
      },
      "parity_loop_family": {
        "local_name": "loop_family",
        "degree_of_freedom": "inductive/deductive parity split",
        "observable": "parity"
      },
      "single_line_change_order": {
        "local_name": "line_order_class",
        "degree_of_freedom": "which single line changes at each step",
        "observable": "changed_line_from_previous"
      },
      "line_flip_operator_family": {
        "local_name": "operator_mode",
        "degree_of_freedom": "line flip as local operator",
        "observable": "Hamming-1 transition"
      },
      "successor_precedence_orientation": {
        "local_name": "precedence_orientation",
        "degree_of_freedom": "directed order of the 64-state walk",
        "observable": "Gray-code successor relation"
      }
    },
    "degrees_of_freedom": [
      "six_line_state",
      "lower_trigram",
      "upper_trigram",
      "line_flip_operator",
      "schedule_direction",
      "parity_loop_family",
      "precedence_order"
    ],
    "state_count": 64
  },
  "cycle_invariant_rows": [
    {
      "slot": "dual_loop",
      "heat_work_cycle": "work-producing/work-consuming traversal",
      "measure_feedback_cycle": "measurement-feedback-erasure/recovery traversal",
      "six_bit_cycle": "odd/even parity loop family on a 64-state walk",
      "boundary": "shared two-direction grammar, not identity"
    },
    {
      "slot": "operator",
      "heat_work_cycle": "thermal contact or adiabatic work leg",
      "measure_feedback_cycle": "correlate, feedback, reset",
      "six_bit_cycle": "single-line flip operator",
      "boundary": "symbolic line flips are not physical operators"
    },
    {
      "slot": "geometry",
      "heat_work_cycle": "four-state cycle",
      "measure_feedback_cycle": "protocol path and memory carrier",
      "six_bit_cycle": "six-bit hypercube Hamiltonian cycle",
      "boundary": "hypercube schedule is not a GStack"
    },
    {
      "slot": "local_invariant_map",
      "heat_work_cycle": "local thermodynamic invariant slots",
      "measure_feedback_cycle": "local information invariant slots",
      "six_bit_cycle": "six lines plus derived precedence relation",
      "boundary": "invariant slots are comparison slots only"
    }
  ],
  "graveyard_variants": [
    {
      "variant": "binary_count_order",
      "reason": "ordinary binary count causes multi-line jumps",
      "unique_states": 64,
      "max_hamming_step": 6,
      "survives_single_line_gate": false,
      "status": "killed"
    },
    {
      "variant": "collapsed_single_state",
      "reason": "all structure collapses to one state",
      "unique_states": 1,
      "max_hamming_step": 0,
      "survives_single_line_gate": false,
      "status": "killed"
    },
    {
      "variant": "seeded_random_order",
      "reason": "random order loses local line-flip grammar",
      "unique_states": 64,
      "max_hamming_step": 6,
      "survives_single_line_gate": false,
      "status": "killed"
    }
  ]
};
