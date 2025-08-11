\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% playable-event? の動作テスト
#(test-ok
  playable-event?
  `(
    ;; NoteEvent → true
    ((,(expected-note-event 0 "4" 'default)) . #t)

    ;; RestEvent → true
    ((,(expected-rest-event "8")) . #t) ; 8分休符

    ;; SkipEvent → true
    ((,(expected-skip-event "8")) . #t) ; 8分の非表示休符

    ;; BarCheck → true
    ((,(expected-bar-check)) . #t)

    ;; その他（非音符系）→ false
    ((42) . #f)
    (("playable?") . #f)
    ((#f) . #f)
    ((()) . #f)
  )
)