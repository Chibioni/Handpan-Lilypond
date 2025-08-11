\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% pitch-translate が使うテーブルを設定
#(set-translate-table '(
    ( 1 .  0)  ; tone-num 1 → pitch 0
    ( 4 .  4)  ; tone-num 4 → pitch 4
    ( 6 .  6)  ; tone-num 6 → pitch 6
    (12 . 12)  ; tone-num 12 → pitch 12
))

%----------------------------------------
% 正常系テスト
%----------------------------------------
#(test-ok
  parse-note-element
  `(
      (("4-4")     . ,(make-custom-note 4 "4" 'default 'HANDPAN-TYPE-NORMAL))
      (("6-8")     . ,(make-custom-note 6 "8" 'default 'HANDPAN-TYPE-NORMAL))

      (("12!-4")   . ,(make-custom-note 12 "4" 'default 'HANDPAN-TYPE-ACCENT))
      (("4!-8")    . ,(make-custom-note  4 "8" 'default 'HANDPAN-TYPE-ACCENT))

      (("6.-4")    . ,(make-custom-note  6 "4" 'default 'HANDPAN-TYPE-GHOST))
      (("12.-8")   . ,(make-custom-note 12 "8" 'default 'HANDPAN-TYPE-GHOST))

      (("12^1-4")  . ,(make-custom-note 12 "4" 'harmonic       'HANDPAN-TYPE-NORMAL))
      (("12^2-8")  . ,(make-custom-note 12 "8" 'harmonic-black 'HANDPAN-TYPE-NORMAL))
      (("R-4")     . ,(make-rest-note      "4"))
      (("H-8")     . ,(make-hide-rest-note "8"))
  )
)

%----------------------------------------
% 異常系テスト
%----------------------------------------
#(test-error
  parse-note-element
  '(
    ;; 引数が文字列でない
    (#t)
    (123)
    ((1 2))

    ;; "-"が含まれない
    ("4")
    ("R")
    ("12^2!")

    ;; duration が数値でない
    ("4-four")
    ("R-four")

    ;; 未知の先頭文字
    ("X-4")

    ;; pitch-translate が失敗するケース（存在しないトーン番号）
    ("99-4")
  )
)