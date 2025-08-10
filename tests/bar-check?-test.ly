\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"

% bar-check? の動作テスト
#(test-ok
  bar-check?
  `(
    ((,(expected-bar-check)) . #t)
    ((,(expected-note-event 0 4 'default)) . #f)
    ((42) . #f)
    (("bar") . #f)
    ((#f) . #f)
    ((()) . #f)
  )
)