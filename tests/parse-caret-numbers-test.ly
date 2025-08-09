\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"


% parse-caret-numbers 正常な引数のテスト
#(test-ok 
    parse-caret-numbers 
    '(  (("1")    . (1   . default )) 
        (("100")  . (100 . default )) 
        (("1^1")  . (1   . harmonic)) 
        (("20^2") . (20  . harmonic-black)) 
    )
)

% parse-caret-numbers 異常な引数のテスト
#(test-error
    parse-caret-numbers
    '(  (#t)
        (#f)
        (100)
        ()
    )
)