\version "2.24.4"

\include "test-functions.ily"
\include "../Handpan.ily"
\include "utils/utility-functions.ily"
\include "utils/test-variables.ly"
\include "utils/expected-articulation-note-list.ily"

% テスト用 articulation
#(define test-articulation (make-music 'ArticulationEvent 'articulation-type 'accent))

% テスト用 BeamEvent
#(define test-beam-event (make-music 'BeamEvent 'span-direction -1))

% case 2: EventChord を末尾に含むリスト
#(define case2-input
  (list (expected-note-event 0 "8" 'normal)
        (expected-accent-note 2 "8" 'default)))

#(define case2-expected
  (let* ((chord    (expected-accent-note 2 "8" 'default))
         (new      (ly:music-deep-copy chord))
         (existing (or (ly:music-property new 'articulations) '())))
    (ly:music-set-property! new 'articulations (append existing (list test-articulation)))
    (list (expected-note-event 0 "8" 'normal) new)))

% case 3: BeamEvent が混在するリスト
#(define case3-input
  (list test-beam-event
        (expected-note-event 0 "8" 'normal)
        (expected-note-event 2 "8" 'normal)))

#(define case3-expected
  (let* ((note     (expected-note-event 2 "8" 'normal))
         (new      (ly:music-deep-copy note))
         (existing (or (ly:music-property new 'articulations) '())))
    (ly:music-set-property! new 'articulations (append existing (list test-articulation)))
    (list test-beam-event (expected-note-event 0 "8" 'normal) new)))

% add-articulation-to-last 正常時のテスト
#(test-ok
    add-articulation-to-last
    `(
        ;; NoteEvent のみのリスト → 末尾 NoteEvent に追加
        ((,test-note-list ,test-articulation) . ,(expected-articulation-note-list test-articulation))

        ;; EventChord を末尾に含むリスト → 末尾 EventChord に追加
        ((,case2-input ,test-articulation) . ,case2-expected)

        ;; BeamEvent が混在するリスト → BeamEvent を読み飛ばして末尾 NoteEvent に追加
        ((,case3-input ,test-articulation) . ,case3-expected)
    )
)

% add-articulation-to-last 異常時のテスト
#(test-error
  add-articulation-to-last
  `(
     ;; music-list が空
     (() ,test-articulation)

     ;; NoteEvent も EventChord も含まないリスト（全て休符）
     ((,(expected-rest-event "4")) ,test-articulation)
     ((,(expected-skip-event "4")) ,test-articulation)
     ((,(expected-bar-check))      ,test-articulation)

     ;; articulation-music が music ではない
     (,test-note-list "not-a-music-object")
     (,test-note-list 123)
   )
)
