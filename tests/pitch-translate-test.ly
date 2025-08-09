\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"

% pitch-translateのテスト
#(define kurd-test '(
  (1 . -1) (2 . 1) (3 . 2)
  (4 .  3) (5 . 4) (6 . 5)
  (7 .  6) (8 . 7) (9 . 8)
))

#(set-translate-table kurd-test)

% pitch-translate 正常な引数のテスト
#(test-ok
    pitch-translate
    '(  ((1) . -1) 
        ((2) .  1) 
        ((3) .  2)
        ((4) .  3) 
        ((5) .  4) 
        ((6) .  5)
        ((7) .  6) 
        ((8) .  7) 
        ((9) .  8)
    )
)

% pitch-translate 異常な値のテスト
#(test-error
    pitch-translate
    '(  ()
        (#t)
        (#f)
        ("error")
        (10)
    )
)