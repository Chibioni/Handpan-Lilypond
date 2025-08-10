\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% skip-event? の動作テスト
#(test-ok
  skip-event?
  `(
    ((,(expected-skip-event 8)) . #t) ; 8分休符
    ((,(expected-note-event 0 4 'default)) . #f)
    ((42) . #f)
    (("rest") . #f)
    ((#f) . #f)
    ((()) . #f)
  )
)
