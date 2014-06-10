# -*- coding: utf-8 -*-
'''
Ranking code based on:
  https://github.com/coleifer/peewee/blob/master/playhouse/sqlite_ext.py
'''


import struct
import math


def parseMatchInfo(buf):
    '''see http://sqlite.org/fts3.html#matchinfo'''
    bufsize = len(buf)  # length in bytes
    return [struct.unpack('@I', buf[i:i+4])[0] for i in range(0, bufsize, 4)]


def simple(raw_match_info):
    '''
    handle match_info called w/default args 'pcx' - based on the example rank
    function http://sqlite.org/fts3.html#appendix_a
    '''
    match_info = parseMatchInfo(raw_match_info)
    score = 0.0
    p, c = match_info[:2]
    for phrase_num in range(p):
        phrase_info_idx = 2 + (phrase_num * c * 3)
        for col_num in range(c):
            col_idx = phrase_info_idx + (col_num * 3)
            x1, x2 = match_info[col_idx:col_idx + 2]
            if x1 > 0:
                score += float(x1) / x2
    return score


def bm25(raw_match_info, column_index, k1=1.2, b=0.75):
    """
    FTS4-only ranking function.

    Usage:

        # Format string *must* be pcxnal
        # Second parameter to bm25 specifies the index of the column, on
        # the table being queries.

        bm25(matchinfo(document_tbl, 'pcxnal'), 1) AS rank
    """
    match_info = parseMatchInfo(raw_match_info)
    score = 0.0
    # p, 1 --> num terms
    # c, 1 --> num cols
    # x, (3 * p * c) --> for each phrase/column,
    #     term_freq for this column
    #     term_freq for all columns
    #     total documents containing this term
    # n, 1 --> total rows in table
    # a, c --> for each column, avg number of tokens in this column
    # l, c --> for each column, length of value for this column (in this row)
    # s, c --> ignore
    p, c = match_info[:2]
    n_idx = 2 + (3 * p * c)
    a_idx = n_idx + 1
    l_idx = a_idx + c
    n = match_info[n_idx]
    a = match_info[a_idx: a_idx + c]
    l = match_info[l_idx: l_idx + c]

    total_docs = n
    avg_length = float(a[column_index])
    doc_length = float(l[column_index])
    if avg_length == 0:
        D = 0
    else:
        D = 1 - b + (b * (doc_length / avg_length))

    for phrase in range(p):
        # p, c, p0c01, p0c02, p0c03, p0c11, p0c12, p0c13, p1c01, p1c02, p1c03..
        # So if we're interested in column <i>, the counts will be at indexes
        x_idx = 2 + (3 * column_index * (phrase + 1))
        term_freq = float(match_info[x_idx])
        term_matches = float(match_info[x_idx + 2])

        # The `max` check here is based on a suggestion in the Wikipedia
        # article. For terms that are common to a majority of documents, the
        # idf function can return negative values. Applying the max() here
        # weeds out those values.
        idf = max(
            math.log(
                (total_docs - term_matches + 0.5) /
                (term_matches + 0.5)),
            0)

        denom = term_freq + (k1 * D)
        if denom == 0:
            rhs = 0
        else:
            rhs = (term_freq * (k1 + 1)) / denom

        score += (idf * rhs)

    return score
