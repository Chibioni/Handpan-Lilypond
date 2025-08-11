\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"
\include "utils/expected-articulation-note-list.ily"

% テスト用 articulation
#(define test-articulation (make-music 'ArticulationEvent 'articulation-type 'accent))

% add-articulation-to-last 正常時のテスト
#(test-ok
    add-articulation-to-last
    `(
        ((,test-note-list ,test-articulation) . ,(expected-articulation-note-list test-articulation))
    )
)

% add-articulation-to-last 異常時のテスト
#(test-error
  add-articulation-to-last
  `(
     ;; music-list が空
     (() ,test-articulation)

     ;; music-list が全てNoteEvent以外（ここでは全て休符など）
     ((,(expected-rest-event "4")) ,test-articulation)
     ((,(expected-skip-event "4")) ,test-articulation)
     ((,(expected-bar-check)) ,test-articulation)

     ;; music-list に playable ではない要素が含まれる
     ((1 2 3) ,test-articulation)

     ;; articulation-music が music ではない
     (,test-note-list "not-a-music-object")
     (,test-note-list 123)
   )
)