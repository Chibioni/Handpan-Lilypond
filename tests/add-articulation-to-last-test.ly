\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"
\include "utils/expected-articulation-note-list.ily"

% テスト用 articulation
#(set! test-articulation (make-music 'ArticulationEvent 'articulation-type 'accent))

% add-articulation-to-last 正常時のテスト
#(test-ok
    add-articulation-to-last
    `(
        ((,test-note-list ,test-articulation) . ,expected-articulation-note-list)
    )
)

% add-articulation-to-last 異常な引数のテスト
#(test-error
  add-articulation-to-last
  `(
     ;; music-list が空
     (() ,test-articulation)

     ;; music-list に NoteEvent 以外が含まれる
     ((1 2 3) ,test-articulation)
     ((,(make-music 'RestEvent)) ,test-articulation)

     ;; articulation-music が music ではない
     (,test-note-list "not-a-music-object")
     (,test-note-list 123)
   )
)

