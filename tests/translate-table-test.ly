\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"

% translate-table 初期値のテスト
#(value-test translate-table '())

% set-translate-table 正常な引数のテスト
#(test-ok
    set-translate-table
    '(  (((1 2 3)) . #t)
        ((("a" "b" "c")) . #t)
    )
)

% set-translate-table 異常な引数のテスト
#(test-error
    set-translate-table
    '(  ()
        (#t)
        (#f)
        ("error")
        (100)
    )
)

% set-translate-table 後の translate-tableのテスト
#(set-translate-table '(1 2 3 4 5))
#(value-test translate-table '(1 2 3 4 5))

