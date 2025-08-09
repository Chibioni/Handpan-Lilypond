\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"


% caret-position 正常な引数のテスト
#(test-ok 
    caret-position 
    '(  (("^")    . 0)
        (("1^")   . 1)
        (("1^2")  . 1)
        (("10^1") . 2)
        (("-1")   . -1)
    ) 
)

% caret-position 異常な引数のテスト
#(test-error
    split-element
    '(  (#t)
        (#f)
        (100)
        ()
    )
)