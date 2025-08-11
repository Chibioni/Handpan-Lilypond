\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"

% note-event-list? の動作テスト
#(test-ok
  note-event-list?
  `(
    ((,test-note-list) . #t)
    ((,(list (expected-note-event 0 "8" 'normal) 99 "invalid")) . #f)
    (((1 2 3)) . #f)
    ((("A" "B")) . #f)
    ((()) . #f)
    ((#f) . #f)
  )
)

