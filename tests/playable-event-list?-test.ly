\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"

% playable-event-list? の動作テスト
#(test-ok
  playable-event-list?
  `(
    ;; ✅ 全部 playable-event → true
    (((,(expected-note-event 0 "4" 'default)
       ,(expected-rest-event "8")
       ,(expected-skip-event "16")
       ,(expected-bar-check))) . #t)

    ;; ❌ 1つでも非playable-event → false
    (((,(expected-note-event 0 "4" 'default)
       42
       ,(expected-rest-event "2"))) . #f)

    ;; ❌ 空リスト → false
    ((()) . #f)

    ;; ❌ リストでない → false
    ((,(expected-note-event 0 "4" 'default)) . #f) ; 単独オブジェクト
    ((42) . #f)
    (("list") . #f)
    ((#f) . #f)
  )
)