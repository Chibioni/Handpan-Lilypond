\version "2.24.4"

% note系テスト用ユーティリティ関数群
#(define (make-test-pitch pitch)
  (ly:make-pitch 0 pitch NATURAL))

#(define (make-test-duration dur)
  (make-duration-obj dur))

#(define (make-test-tweaks style)
  (list (cons 'style style)))

#(define (expected-note-event pitch duration style)
  (make-music
    'NoteEvent
    'pitch (make-test-pitch pitch)
    'duration (make-test-duration duration)
    'tweaks (make-test-tweaks style)
  ))

