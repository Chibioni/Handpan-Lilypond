\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% note-event? の動作テスト
#(test-ok
  note-event?
  `(
    ((,(expected-note-event 0 "4" 'default)) . #t)
    ((42) . #f)
    (("note") . #f)
    ((#f) . #f)
    ((()) . #f)
  )
)