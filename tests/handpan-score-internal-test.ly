\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"

% ===== モック関数で依存関数を置き換え =====
#(set! split-score
   (lambda (score-str) 
    (string-split score-str #\space) ; 空白で分割
   )
)

#(set! parse-token-list
   (lambda (tokens)
     (map (lambda (tok) (string-append "PARSED:" tok)) tokens)))

#(set! make-sequential-music
   (lambda (notes)
     (string-append "SEQ:" (string-join notes ","))))

% ===== 正常系のテスト =====
#(test-ok
  handpan-score-internal
  `(
    ;; 単純なスコア文字列
    (("6^2!-8 4-4 R-8") . "SEQ:PARSED:6^2!-8,PARSED:4-4,PARSED:R-8")

    ;; 空文字列（空リストに展開される）
    (("") . "SEQ:PARSED:")

    ;; ひとつだけのトークン
    (("12!-4") . "SEQ:PARSED:12!-4")
  )
)

% ===== 異常系テスト =====
#(test-error
  handpan-score-internal
  '(
    ;; 引数が数値
    (123)

    ;; 引数がリスト
    (("6^2!-8" "4-4"))

    ;; 引数が #t (boolean)
    (#t)

    ;; 引数が #f (boolean)
    (#f)

    ;; 引数が空リスト
    (())
  )
)
