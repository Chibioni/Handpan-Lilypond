\version "2.24.4"

\include "utility-functions.ily"

% テスト用のノートリスト
#(define test-note-list
  (list
    (expected-note-event 0 8 'normal)
    (expected-note-event 2 8 'normal)
    (expected-note-event 4 8 'normal)
  ))

