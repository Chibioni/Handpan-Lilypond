\version "2.24.4"

% note系テスト用ユーティリティ関数群

#(define (make-test-pitch pitch)
  (ly:make-pitch 0 pitch NATURAL))

#(define (make-test-duration dur)
  (make-duration-obj dur))

#(define (make-test-tweaks style)
  (list (cons 'style style)))

% 想定される音符イベントを作成する
#(define (expected-note-event pitch duration style)
  (make-music
    'NoteEvent
    'pitch (make-test-pitch pitch)
    'duration (make-test-duration duration)
    'tweaks (make-test-tweaks style)
  ))

% 想定されるアクセント付き音符イベントを作成する
#(define (expected-accent-note pitch duration style)
  (make-music
    'EventChord
    'elements (list (expected-note-event pitch duration style))
    'articulations (list (make-music 'ArticulationEvent 'articulation-type 'accent))
  )
)

% 想定されるゴーストノートイベントを作成する
#(define (expected-ghost-note pitch duration style)
  (let* (
      (base (expected-note-event pitch duration style))
      (small (begin
               (ly:music-set-property! base 'tweaks (append
                 (ly:music-property base 'tweaks)
                 (list (cons 'font-size -3) (cons 'parenthesized #t))
               ))
               base))
    )
    (make-music
      'EventChord
      'elements (list small)
      'tweaks (list (cons 'parenthesized #t))
    )
  )
)

% バーチェック(小節線)のテスト用オブジェクト
#(define (expected-bar-check)
  (make-music 'BarCheck))

% 休符(RestEvent)のテスト用オブジェクト
#(define (expected-rest-event duration)
  ;; duration-log は 4分音符なら 2、8分音符なら 3 など
  ;; dots は付点の数
  (make-music 'RestEvent
              'duration (make-test-duration duration))
)

% 非表示休符(SkipEvent)のテスト用オブジェクト
#(define (expected-skip-event duration)
  (make-music 'SkipEvent
              'duration (make-test-duration duration))
)

% タイ付き NoteEvent を生成するヘルパー
#(define (expected-note-with-tie pitch duration style)
  (let* ((note      (expected-note-event pitch duration style))
         (tie-event (make-music 'TieEvent)))
    (ly:music-set-property! note 'articulations (list tie-event))
    note))

% タイ付き EventChord を生成するヘルパー（アクセント・ゴースト・和音）
#(define (expected-chord-with-tie music)
  (let* ((new-music (ly:music-deep-copy music))
         (existing  (or (ly:music-property new-music 'articulations) '()))
         (tie-event (make-music 'TieEvent)))
    (ly:music-set-property! new-music 'articulations (append existing (list tie-event)))
    new-music))
