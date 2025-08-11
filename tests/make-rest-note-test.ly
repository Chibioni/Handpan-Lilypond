\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"

% make-rest-note 正常な引数のテスト（文字列化）
#(test-ok
    make-rest-note
    `(
        (("4")  . ,(make-music 'RestEvent 'duration (make-duration-obj "4")))
        (("8")  . ,(make-music 'RestEvent 'duration (make-duration-obj "8")))
        (("16") . ,(make-music 'RestEvent 'duration (make-duration-obj "16")))
        (("32") . ,(make-music 'RestEvent 'duration (make-duration-obj "32")))
        (("4.")  . ,(make-music 'RestEvent 'duration (make-duration-obj "4.")))   ; 付点休符
        (("8..") . ,(make-music 'RestEvent 'duration (make-duration-obj "8..")))  ; 複付点休符
    )
)

% make-rest-note 異常テスト（文字列以外はエラー）
#(test-error
    make-rest-note
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
        ("0.")     ; 0は不正
        ("4a")     ; 不正文字を含む
    )
)