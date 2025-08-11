\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% make-custom-note 正常時のテスト
#(test-ok
  make-custom-note
  `(
      ;; NORMAL
      (( 0 "4" default HANDPAN-TYPE-NORMAL) . ,(expected-note-event 0 "4" 'default))
      ((10 "8" harmonic HANDPAN-TYPE-NORMAL) . ,(expected-note-event 10 "8" 'harmonic))

      ;; ACCENT
      (( 0 "4" default HANDPAN-TYPE-ACCENT) . ,(expected-accent-note 0 "4" 'default))
      (( 5 "8" harmonic HANDPAN-TYPE-ACCENT) . ,(expected-accent-note 5 "8" 'harmonic))

      ;; GHOST
      (( 0 "4" default HANDPAN-TYPE-GHOST) . ,(expected-ghost-note 0 "4" 'default))
      ((-2 "16" harmonic-black HANDPAN-TYPE-GHOST) . ,(expected-ghost-note -2 "16" 'harmonic-black))
  )
)

% make-custom-note 異常な引数のテスト
#(test-error
  make-custom-note
  '(
    ;; 引数不足 / 過剰
    ()
    (60)
    (60 "4")
    (60 "4" 'default)
    (60 "4" 'default HANDPAN-TYPE-NORMAL 'extra)

    ;; pitch が整数でない
    ("C4" "4" 'default HANDPAN-TYPE-NORMAL)
    (#t  "4" 'default HANDPAN-TYPE-NORMAL)

    ;; duration が不正な文字列や型
    (60 "4th" 'default HANDPAN-TYPE-NORMAL)   ; 不正文字列
    (60 #t    'default HANDPAN-TYPE-NORMAL)   ; 型違い

    ;; head-style がシンボルでない
    (60 "4" "default" HANDPAN-TYPE-NORMAL)
    (60 "4" 123       HANDPAN-TYPE-NORMAL)

    ;; note-type が未定義シンボル
    (60 "4" 'default 'UNKNOWN-TYPE)
  )
)
