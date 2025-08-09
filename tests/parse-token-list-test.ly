\version "2.24.4"

\include "../Handpan.ily"
\include "test-functions.ily"

% ===== ダミー関数で依存をモック化 =====
#(set! parse-note-element
  (lambda (s)
    (string-append "NOTE:" s)))

#(set! make-beam-group
  (lambda (notes)
    (string-append "BEAM:" (format #f "~a" notes))))

#(set! make-chord-group
  (lambda (notes)
    (string-append "CHORD:" (format #f "~a" notes))))

#(set! check-bar-line
  (lambda ()
    "BAR"))

% ===== 正常系テスト =====
#(test-ok
  parse-token-list
  `(
    ;; 単音だけ
    ((("1-4" "2-8"))                   . ("NOTE:1-4" "NOTE:2-8"))

    ;; 連桁 [ ] の処理
    ((("[" "1-16" "2-16" "]" "3-4"))   . ("BEAM:(NOTE:1-16 NOTE:2-16)" "NOTE:3-4"))

    ;; 和音 < > の処理
    ((("<" "1-4" "3-4" ">" "5-8"))     . ("CHORD:(NOTE:1-4 NOTE:3-4)" "NOTE:5-8"))

    ;; 小節線 |
    ((("1-4" "|" "2-4"))               . ("NOTE:1-4" "BAR" "NOTE:2-4"))

    ;; 混合ケース
    ((("[" "1-16" "2-16" "]" "<" "3-4" "5-4" ">" "|" "6-4"))
     . ("BEAM:(NOTE:1-16 NOTE:2-16)"
        "CHORD:(NOTE:3-4 NOTE:5-4)"
        "BAR"
        "NOTE:6-4"))
  )
)

% ===== 異常系テスト =====
#(test-error
  parse-token-list
  '(
    ;; 1. 連桁の閉じ記号がない
    (("[" "1-4" "2-4"))

    ;; 2. 和音の閉じ記号がない
    (("<" "1-4" "2-4"))

    ;; 3. 連桁内に禁止トークン "[" が現れる
    (("[" "1-4" "[" "2-4" "]"))

    ;; 4. 和音内に禁止トークン "[" が現れる
    (("<" "1-4" "[" "2-4" ">"))
  )
)