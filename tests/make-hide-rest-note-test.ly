\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"


% make-hide-rest-note 正常な引数のテスト
#(test-ok
    make-hide-rest-note
    `(
        ((4)  . ,(make-music 'SkipEvent 'duration (make-duration-obj 4)))
        ((8)  . ,(make-music 'SkipEvent 'duration (make-duration-obj 8)))
        ((16) . ,(make-music 'SkipEvent 'duration (make-duration-obj 16)))
        ((32) . ,(make-music 'SkipEvent 'duration (make-duration-obj 32)))
    )
)

% make-hide-rest-note 異常な引数のテスト
#(test-error
    make-hide-rest-note
    '(  (#t)
        (#f)
        ("error")
        ()
    )
)