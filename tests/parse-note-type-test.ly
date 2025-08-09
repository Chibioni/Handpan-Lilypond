\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"

% parse-note-type 正常な引数のテスト
#(test-ok
    parse-note-type
    '(  ((".")    . (""    . HANDPAN-TYPE-GHOST))
        (("1.")   . ("1"   . HANDPAN-TYPE-GHOST))
        (("100.") . ("100" . HANDPAN-TYPE-GHOST))

        (("!")    . (""    . HANDPAN-TYPE-ACCENT))
        (("1!")   . ("1"   . HANDPAN-TYPE-ACCENT))
        (("100!") . ("100" . HANDPAN-TYPE-ACCENT))

        (("")    . (""    . HANDPAN-TYPE-NORMAL))
        (("1")   . ("1"   . HANDPAN-TYPE-NORMAL))
        (("100") . ("100" . HANDPAN-TYPE-NORMAL))
    )
)