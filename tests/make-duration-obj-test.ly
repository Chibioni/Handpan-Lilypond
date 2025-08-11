\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"

% make-duration-obj 正常な引数のテスト（文字列化）
#(test-ok 
    make-duration-obj 
    `(
        (("4")  . ,(ly:make-duration 2 0))
        (("8")  . ,(ly:make-duration 3 0))
        (("16") . ,(ly:make-duration 4 0))
        (("32") . ,(ly:make-duration 5 0))
        (("4.")  . ,(ly:make-duration 2 1))   ; 付点4分音符
        (("8..") . ,(ly:make-duration 3 2))   ; 複付点8分音符
    )
)

% make-duration-obj 異常テスト
#(test-error
    make-duration-obj
    '(
        ; 文字列以外はエラー
        (#t)
        (#f)
        (4)        ; 整数はエラー
        (8.0)      ; 実数はエラー
        ('symbol)  ; シンボルはエラー
        ()         ; 引数なし
        ; 無効な文字列のエラー
        ("error")  ; 数字がない
        ("4a")     ; 数字部分が混ざっている
        ("0.")     ; 0は不正
 
    )
)