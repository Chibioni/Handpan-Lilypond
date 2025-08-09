\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"


% make-duration-obj 正常な引数のテスト
#(test-ok 
    make-duration-obj 
    `(
        ((4) .  ,(ly:make-duration 2 0))
        ((8) .  ,(ly:make-duration 3 0))
        ((16) . ,(ly:make-duration 4 0))
        ((32) . ,(ly:make-duration 5 0))
    )
)

% make-duration-obj 異常な型のテスト
#(test-error
    make-duration-obj
    '(  (#t)
        (#f)
        ("error")
        ()
    )
)