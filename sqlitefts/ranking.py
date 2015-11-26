# -*- coding: utf-8 -*-
'''
Ranking code based on:
  https://github.com/coleifer/peewee/blob/master/playhouse/sqlite_ext.py
'''


import struct
import math


def _parse_match_info(buf):
    # See http://sqlite.org/fts3.html#matchinfo
    bufsize = len(buf)  # Length in bytes.
    return [struct.unpack('@I', buf[i:i+4])[0] for i in range(0, bufsize, 4)]


# Ranking implementation, which parse matchinfo.
def rank(raw_match_info, *weights):
    # Handle match_info called w/default args 'pcx' - based on the example rank
    # function http://sqlite.org/fts3.html#appendix_a
    match_info = _parse_match_info(raw_match_info)
    score = 0.0

    p, c = match_info[:2]
    if not weights:
        weights = [1] * c
    else:
        weights = [0] * c
        for i, weight in enumerate(weights):
            weights[i] = weight

    for phrase_num in range(p):
        phrase_info_idx = 2 + (phrase_num * c * 3)
        for col_num in range(c):
            weight = weights[col_num]
            if not weight:
                continue

            col_idx = phrase_info_idx + (col_num * 3)
            x1, x2 = match_info[col_idx:col_idx + 2]
            if x1 > 0:
                score += weight * (float(x1) / x2)

    return -score

simple = rank


# Okapi BM25 ranking implementation (FTS4 only).
def bm25(raw_match_info, *args):
    """
    Usage:
        # Format string *must* be pcnalx
        # Second parameter to bm25 specifies the index of the column, on
        # the table being queries.
        bm25(matchinfo(document_tbl, 'pcnalx'), 1) AS rank
    """
    match_info = _parse_match_info(raw_match_info)
    K = 1.2
    B = 0.75
    score = 0.0

    P_O, C_O, N_O, A_O = range(4)
    term_count = match_info[P_O]
    col_count = match_info[C_O]
    total_docs = match_info[N_O]
    L_O = A_O + col_count
    X_O = L_O + col_count

    if not args:
        weights = [1] * col_count
    else:
        weights = [0] * col_count
        for i, weight in enumerate(args):
            weights[i] = args[i]

    for i in range(term_count):
        for j in range(col_count):
            weight = weights[j]
            if weight == 0:
                continue

            avg_length = float(match_info[A_O + j])
            doc_length = float(match_info[L_O + j])
            if avg_length == 0:
                D = 0
            else:
                D = 1 - B + (B * (doc_length / avg_length))

            x = X_O + (3 * j * (i + 1))
            term_frequency = float(match_info[x])
            docs_with_term = float(match_info[x + 2])

            idf = max(
                math.log(
                    (total_docs - docs_with_term + 0.5) /
                    (docs_with_term + 0.5)),
                0)
            denom = term_frequency + (K * D)
            if denom == 0:
                rhs = 0
            else:
                rhs = (term_frequency * (K + 1)) / denom

            score += (idf * rhs) * weight

    return -score
