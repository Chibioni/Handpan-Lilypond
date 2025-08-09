\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"

% split-score 正常時のテスト
#(test-ok
    split-score 
    '(  (( "a b c" ) . ("a" "b" "c"))
        (( "R-8" )   . ("R-8"))
        (( "6^2!-8 4-4 R-8" ) . ("6^2!-8" "4-4" "R-8"))
        (("") . ())
    )
)

% split-score 異常な引数のテスト
#(test-error
    split-score
    '(  (1234)
        (#t)
        (#f)
        ()
    )
)



