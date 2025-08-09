\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"


% split-element 正常な引数のテスト
#(test-ok
    split-element
    '(  (( "1-2" ) . ("1" "2"))
        (( "R-8" )   . ("R" "8"))
        (( "6^2!-8" ) . ("6^2!" "8"))
    )
)

% split-element 異常な引数のテスト
#(test-error
    split-element
    '(  (#t)
        (#f)
        ()
        ("error")
    )
)