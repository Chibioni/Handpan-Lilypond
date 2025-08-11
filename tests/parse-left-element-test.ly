\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% pitch-translate が使うテーブルを設定
#(set-translate-table '(
    (1 . 0)    ; tone-num 1 → pitch 0
    (4 . 4)    ; tone-num 4 → pitch 4
    (6 . 6)    ; tone-num 6 → pitch 6
    (12 . 12)  ; tone-num 12 → pitch 12
))

%----------------------------------------
% 正常系テスト
%----------------------------------------
#(test-ok
  parse-left-element
  `(
      ;; --- Slap (符頭 cross) ---
      (("S4"    "4") . ,(make-custom-note  4  "4" 'cross 'HANDPAN-TYPE-NORMAL))
      (("S12!"  "8") . ,(make-custom-note 12  "8" 'cross 'HANDPAN-TYPE-ACCENT))
      (("S6."  "16") . ,(make-custom-note  6 "16" 'cross 'HANDPAN-TYPE-GHOST))

      ;; --- Apex ring (符頭 xcircle) ---
      (("O4"    "4") . ,(make-custom-note  4  "4" 'xcircle 'HANDPAN-TYPE-NORMAL))
      (("O12!"  "8") . ,(make-custom-note 12  "8" 'xcircle 'HANDPAN-TYPE-ACCENT))
      (("O6."  "16") . ,(make-custom-note  6 "16" 'xcircle 'HANDPAN-TYPE-GHOST))

      ;; --- Rest ---
      (("R" "4")      . ,(make-rest-note "4"))
      (("R" "8")      . ,(make-rest-note "8"))

      ;; --- HideRest ---
      (("H"  "4")      . ,(make-hide-rest-note "4"))
      (("H" "16")     . ,(make-hide-rest-note "16"))

      ;; --- Tone field (通常) ---
      (("4"    "4") . ,(make-custom-note  4  "4" 'default 'HANDPAN-TYPE-NORMAL))
      (("6!"   "8") . ,(make-custom-note  6  "8" 'default 'HANDPAN-TYPE-ACCENT))
      (("12." "16") . ,(make-custom-note 12 "16" 'default 'HANDPAN-TYPE-GHOST))

      ;; --- Harmonics ---
      (("12^1" "4")  . ,(make-custom-note 12 "4" 'harmonic       'HANDPAN-TYPE-NORMAL))
      (("12^2" "8")  . ,(make-custom-note 12 "8" 'harmonic-black 'HANDPAN-TYPE-NORMAL))
  )
)

%----------------------------------------
% 異常系テスト
%----------------------------------------
#(test-error
  parse-left-element
  '(
    ;; 引数型不正
    (#t 4)                  ; note-str が文字列でない
    ("4" #t)                ; duration が文字列でない
    ("4" 4)                 ; duration が数値

    ;; 空文字列
    ("" 4)

    ;; 未知の先頭文字
    ("X12" 4)

    ;; pitch-translate で失敗（トーン番号がテーブルにない）
    ("99" 4)
    ("S99" 4)
    ("O99" 4)

    ;; caret 番号が1,2以外
    ("12^3" 4)
  )
)
