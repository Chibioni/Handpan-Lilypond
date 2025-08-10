#(ly:set-option 'compile-scheme-code)
#(debug-enable 'backtrace)

\version "2.24.4"

% LilyPond 側から\HandpanScore で使えるように設定
HandpanScore =
#(define-music-function (parser location str) (string?)
   (handpan-score-internal str)
)

SetTranslateTable =
#(define-music-function
  (table)
  (scheme?)
  (begin
    (set-translate-table table)
    (make-music 'Music)) ;; 空の音楽を返す（副作用だけなので）
)

% 与えられたスコア文字列（"6^2!-8 4-4 R-8"など）を LilyPond 音楽オブジェクトへ変換する
% テスト書いた
#(define (handpan-score-internal score-str)
  (if (not (string? score-str))
    (error "parse-score: 引数が文字列ではありません")
    (let* (
        (tokens (split-score score-str))      ; 例: '("6^2!-8" "4-4" "R-8")
        (notes (parse-token-list tokens))     ; 各トークンを解析して音符を生成
        (music (make-sequential-music notes)) ; 音符を順に並べた音楽オブジェクトを作成
      )
      music
    )
  )
)

% translate-table の宣言
% 定義してなければ空リスト
%テスト書いた
#(define translate-table '())

% translate-table を書き換える
% テスト書いた
#(define (set-translate-table table)
  (cond 
    (     (null? table)  (error "set-translate-table: table is empty"))
    ((not (list? table)) (error "set-translate-table: table is not a list"))
    (else
      (set! translate-table table)
      #t
    )
  )
)

% translate-table を使って、ハンドパンのトーンフィールド番号を五線譜の音符に変換する
% テスト書いた
#(define (pitch-translate tone-num)
  (cond
    (     (null? translate-table)  (error "pitch-translate: translate-table is empty"))
    ((not (list? translate-table)) (error "pitch-translate: translate-table is not a list"))
    ((not (integer? tone-num))     (error "pitch-translate: pitch is not an integer"))
    (else
      (let (
          (pitch-pair (assoc tone-num translate-table))
        )
        (if (not pitch-pair)
          (error "pitch-translate: tone-num does not exist")
          (cdr pitch-pair)
        )
      )
    )
  )
)

% "6^2!-8 4-4 R-8" といった楽譜から1音符ずつのリストにする
% -> ( "6^2!-8" "4-4" "R-8" )
%テスト書いた
#(define (split-score string-score)
  (if (not (string? string-score))
    (error "split-score: string-score is not a string" string-score)
    (let ((tokens (string-tokenize string-score)))
      tokens
    )
  )
)



% リストから見つけた記号に合わせた処理関数へ処理を移譲する
% テスト書いた
#(define (parse-token-list tokens)
  (let loop ((tokens tokens) (result '()))
    (cond 
      ( (null? tokens)
        (reverse result)
      )

      ; 連桁の処理
      ( (string=? (car tokens) "[")
        (let* (
            (parsed (parse-block (cdr tokens) "]" '("["))) ; ("[" "1-16" "2!-16" "3.-16" "]" "5-4" ) -> ( ("1-16" "2!-16" "3.-16") . ("5-4") )
            (beam-notes (car parsed)) ; ("1-16" "2!-16" "3.-16")
            (rest (cdr parsed))       ; ("5-4")
            (parsed-beam-notes (parse-token-list beam-notes)) ; beam-notes 内の和音を処理する(lilypondノートのリストになる)
            (beam-music (make-beam-group parsed-beam-notes))
          )
          (loop rest (cons beam-music result))
        )
      )

      ; 和音の処理
      ( (string=? (car tokens) "<")
        (let* (
            (parsed (parse-block (cdr tokens) ">" '("<" "[" "]"))) ; ("<" "1-16" "3!-16" "5.-16" ">" "5-4" ) -> ( ("1-16" "3!-16" "5.-16") . ("5-4") )
            (chord-notes-list (car parsed)) ; ("1-16" "2!-16" "3.-16")
            (rest (cdr parsed))       ; ("5-4")
            (chord-notes (map parse-note-element chord-notes-list)) ; lilypondノートに変換
            (chord-music (make-chord-group chord-notes))
          )
          (loop rest (cons chord-music result))
        )
      )
      
      ; 小節線のチェック
      ( (string=? (car tokens) "|")
        (let* (
          (rest (cdr tokens))
        )
        (loop rest (cons (check-bar-line) result))
        )
      )


      (else
        (loop (cdr tokens) (cons (parse-note-element (car tokens)) result)))))
)

% 連桁や和音のまとまりを検出して返す
% tokens        : 楽譜用の記号を記述した文字列のリスト
% end-token     : グループの終端を表す記号の文字列... "]", ">", ...
% ignore-tokens : グループ内に存在してはならない記号のリスト
% テスト書いた
#(define (parse-block tokens end-token ignore-tokens)
  (let loop ((tokens tokens) (collected '()))
    (cond

      ;; トークンが尽きた＝閉じ記号が見つからない
      ( (null? tokens)
        (error (string-append "parse-block: 終端記号 '" end-token "' が見つかりません"))
      )

      ;; 閉じ記号に到達した → 結果と残りトークンを返す
      ( (string=? (car tokens) end-token)
        (cons (reverse collected) (cdr tokens))
      )

      ;; 禁止されたトークンを含んでいた場合 → エラー
      ( (member (car tokens) ignore-tokens equal?)
        (error (string-append "parse-block: 許可されていない記号 '" (car tokens) "' がブロック内に現れました"))
      )

      ;; 通常のトークン → 蓄積して次へ
      (else
        (loop (cdr tokens) (cons (car tokens) collected))
      )
    )
  )
)


% 連桁のグループを作成する
% テスト書いた
#(define (make-beam-group notes)
  (make-music
    'SequentialMusic
    'elements
      (append
        (list (make-music 'BeamEvent 'span-direction -1))
        (add-articulation-to-last notes (make-music 'BeamEvent 'span-direction 1) ) ; 最後の要素に連桁の終わりを追加
      )
  )
)

% リスト最後のlilypond要素に、articulationsを追加する
% テスト書いた
#(define (add-articulation-to-last music-list articulation-music)
  (unless (note-event-list? music-list) ;; music-listのチェック
    (error "add-articulation-to-last: music-list must be a non-empty list of NoteEvent music expressions"))
  (unless (ly:music? articulation-music) ;; articulation-musicのチェック
    (error "add-articulation-to-last: articulation-music must be a music expression"))
  (let* (
      (last (car (reverse music-list)))                                    ; 最後の要素を抽出
      (rest (reverse (cdr (reverse music-list))))                          ; 最後以外の要素のリスト
      (existing-artics (ly:music-property last 'articulations))            ; 最後の要素に既に設定されている articulations を取得
      (new-artics (append existing-artics (list articulation-music)))      ; 取得した articulations に追加したい内容を追加
      (new-last (ly:music-set-property! last 'articulations new-artics))   ; 最後の要素の articulations を上書き
    )
    (append rest (list new-last)) ; 元のリストに復元
  )
)

% 和音のグループを作成する
% テスト書いた
#(define (make-chord-group notes)
  (unless (note-event-list? notes)
    (error "make-chord-group: all elements must be NoteEvent music expressions:" notes))
  (make-music
    'EventChord
    'elements notes
  )
)

% ノートイベントなら true, それ以外なら false を返す
% テスト書いた
#(define (note-event? x)
  (and (ly:music? x)
       (eq? (ly:music-property x 'name) 'NoteEvent)))


% バーチェックなら true, それ以外なら false を返す
% テスト書いた
#(define (bar-check? x)
  (and (ly:music? x)
       (eq? (ly:music-property x 'name) 'BarCheck)))

% 休符なら true, それ以外なら false を返す
% テスト書いた
#(define (rest-event? x)
  (and (ly:music? x)
       (eq? (ly:music-property x 'name) 'RestEvent)))

% 非表示休符なら true, それ以外なら false を返す
% テスト書いた
#(define (skip-event? x)
  (and (ly:music? x)
       (eq? (ly:music-property x 'name) 'SkipEvent)))


% ノートイベントのリストなら true, それ以外なら false を返す
% テスト書いた
#(define (note-event-list? lst)
  (and (list? lst)
       (not (null? lst))
       (every note-event? lst)))

% ノートイベント、休符、非表示休符、バーチェックならtrue, それ以外なら false を返す
#(define (playable-event? x)
  (or (note-event? x)
      (rest-event? x)
      (skip-event? x)
      (bar-check?  x)))

%小節線のチェック
%テスト書いた
#(define (check-bar-line)
  (make-music 'BarCheck)
)

% "12^2!-8" という音符を表す文字列から音符を作成する
% テスト書いた
#(define (parse-note-element element-str)
  (if (not (string? element-str)) 
    (error "element-str is not a string")
    (let* (
        (tokens (split-element element-str))      ; -> ("4^2!" "4")
        (left (car tokens))                       ; "4^2!"
        (duration (string->number (cadr tokens))) ; "4" → 4
        (note (parse-left-element left duration)) ; 音符オブジェクト
      )
      note
    )
  )
)

% "12^2!-8" という音高-音価の音符を分割する
% -> ("12^2!" "8")
%テスト書いた
#(define (split-element element)
  (if (not (string? element)) 
    (error "element is not a string")
    (let (
        (tokens (string-split element (string->char-set "-")))
      )
      (if (<= (length tokens) 1) 
        (error "element tokens length <= 1")
        tokens
      )
    )
  )
)



% ここからそれぞれの音符用の処理を書く
% 音符は make-custom-note 関数を用いる
% テスト書いた
#(define (parse-left-element note-str duration)
  (cond
    ((not (string? note-str))
      (error "parse-left-element: 引数1が文字列ではありません"))

    ((not (number? duration))
      (error "parse-left-element: 引数2が数値ではありません"))

    ((= (string-length note-str) 0)
      (error "parse-left-element: 空文字列"))

    ;; Slap
    ((char=? (string-ref note-str 0) #\S)
      (let* (
          (rest-str (substring note-str 1)) ; "S12!" -> "12!"
          (type-pair (parse-note-type rest-str))     ; "12!" -> ("12" . 'HANDPAN-TYPE-ACCENT)
          (tone-num (string->number (car type-pair)))
          (note-type (cdr type-pair))

          (pitch (pitch-translate tone-num))    ; 変換後の五線譜音高
          (head-style 'cross)
        )
        (make-custom-note pitch duration head-style note-type)
      )
    )

    ;; Rest
    ((char=? (string-ref note-str 0) #\R)
      (let (
          (rest-note (make-rest-note duration))
        )
        rest-note
      )
    )

    ;; HideRest
    ((char=? (string-ref note-str 0) #\H)
      (let (
          (hide-rest-note (make-hide-rest-note duration))
        )
        hide-rest-note
      )
    )

    ;; Tone field numbers / Harmonics
    ((char-numeric? (string-ref note-str 0))
      (let* (
          (type-pair (parse-note-type note-str))     ; "12^2!" -> ("12^2" . 'HANDPAN-TYPE-ACCENT)
          (note-body (car type-pair))
          (note-type (cdr type-pair))

          (parsed (parse-caret-numbers note-body))    ; "12^2" => (12 . 'harmonic-black)
          (tone-num (car parsed))
          (head-style (cdr parsed))
          (pitch (pitch-translate tone-num))    ; 変換後の五線譜音高
        )
        (make-custom-note pitch duration head-style note-type)
      )
    )
    (else
      (error (string-append "parse-left-element -> Tonefield : 未知の要素: " note-str))
    )
  )
)

% 音符の種類を定義した定数群
% テスト書いた
#(define HANDPAN-TYPE-NORMAL 'normal)
#(define HANDPAN-TYPE-ACCENT 'accent)
#(define HANDPAN-TYPE-GHOST  'ghost)

% ベーシックな音符を作成する
% pitch      : 音高
% duration   : 音価
% head-style : 符頭の形指定 
%   通常          : 'normal
%   ハーモニクス1 : 'harmonic
%   ハーモニクス2 : 'harmonic-black
% テスト書いた
#(define (make-base-note pitch duration head-style)
  (cond 
    ((not (integer? pitch))
      (error "make-base-note: pitch must be an integer, got:" pitch))
    ((not (symbol? head-style))
      (error "make-base-note: head-style must be a symbol, got:" head-style))
    (else 
      (let* (
          (duration-obj (make-duration-obj duration))
        )
        (make-music
          'NoteEvent
          'pitch (ly:make-pitch 0 pitch NATURAL)
          'duration duration-obj
          'tweaks (list (cons 'style head-style))
        )
      )
    )
  )
)

% 音符を作成する
% pitch           : 音高
% duration        : 音価
% head-style      : 符頭の形指定
% --------------------------------ここまで make-base-noteで利用する
% note-type : 
%   HANDPAN-TYPE-NORMAL : 通常の音符
%   HANDPAN-TYPE-ACCENT : アクセント記号付き
%   HANDPAN-TYPE-GHOST  : ゴースト・ノート
% テスト書いた
#(define (make-custom-note pitch duration head-style note-type)
  (let*
    (
      (note-base (make-base-note pitch duration head-style))
      ;; note-type に応じて加工
      (note-with-modifier
        (cond
          ((eq? note-type 'HANDPAN-TYPE-GHOST)
            (let* 
              (
                (small-note (begin
                  (ly:music-set-property! note-base 'tweaks (append
                    (ly:music-property note-base 'tweaks)
                    (list 
                      (cons 'font-size -3)
                      (cons 'parenthesized #t)
                    )
                  ))
                  note-base
                ))
                (ghost-note (make-music
                  'EventChord
                  'elements (list small-note)
                  'tweaks (list 
                    (cons 'parenthesized #t)

                  )
                ))
              ) 
              ghost-note 
            )
          )

          ((eq? note-type 'HANDPAN-TYPE-ACCENT)
            ;; アクセント：ArticulationEvent を追加
            (make-music
              'EventChord
              'elements (list note-base)
              'articulations
              (list (make-music 'ArticulationEvent 'articulation-type 'accent))
            )
          )

          (else
            ;; 通常音符
            note-base
          )
        )
      )
    )
    note-with-modifier
  )
)

%休符を作る
%テスト書いた
#(define (make-rest-note duration)
  (if (not (integer? duration))
      (error "make-rest-note: duration must be an integer" duration))
  (let* (
      (duration-obj (make-duration-obj duration))
      (rest-note 
        (make-music
          'RestEvent
          'duration duration-obj
        )
      )
    )
    rest-note
  )
)

%非表示休符を作る
%テスト書いた
#(define (make-hide-rest-note duration)
  (if (not (integer? duration))
      (error "make-hide-rest-note: duration must be an integer" duration))
  (let* (
      (duration-obj (make-duration-obj duration))
      (hide-rest-note 
        (make-music
          'SkipEvent
          'duration duration-obj
        )
      )
    )
    hide-rest-note
  )
)

%lilypondのdurationオブジェクトを作成して返す
%テスト書いた
#(define (make-duration-obj duration)
  ;; 整数チェック
  (if (not (integer? duration))
      (error "make-duration-obj: duration must be an integer" duration))
  (let (
      (duration-obj (ly:make-duration (inexact->exact (round (/ (log duration) (log 2)))) 0))
    )
    duration-obj
  )
)

% 文字列に"!"か"."が含まれていた時の処理を行い、記号までの文字列と音符の種類を返す
% テスト書いた
#(define (parse-note-type str)
  (cond
    ;; ゴースト（"." を含む）
    ((string-contains str ".")
      (let (
          (idx (string-index str #\.))
        )
        (cons (substring str 0 idx) 'HANDPAN-TYPE-GHOST)
      )
    )

    ;; アクセント（"!" を含む）
    ((string-contains str "!")
      (let (
          (idx (string-index str #\!))
        )
        (cons (substring str 0 idx) 'HANDPAN-TYPE-ACCENT)
      )
    )

    ;; 通常ノート
    (else
      (cons str 'HANDPAN-TYPE-NORMAL)
    )
  )
)

% 通常の音符、harmonicsの関数----------------------

% "^"が見つかった最初の位置を返す。見つからなかった場合は-1を返す
% テスト書いた
#(define (caret-position str)
  (if (not (string? str))
    (error "caret-position:Argument is not a string.")
    (let ((pos (string-index str #\^)))
      (if pos
        pos
        -1
      )
    )
  )
)

% "10"       -> (10 . 'default)
% "12^1"     -> (12 . 'harmonic)
% "12^2"     -> (12 . 'harmonic-black)
% その他     -> エラー
% テスト書いた
#(define (parse-caret-numbers str)
  (if (not (string? str))
    (error "parse-caret-numbers:Argument is not a string.")
  )
  (let ((pos (caret-position str)))
    (if (= pos -1)
      (cons (string->number str) 'default)
      (let* (
          (before (string->number (substring str 0 pos)))
          (after  (string->number (substring str (+ pos 1))))
        )
        (cons before
          (cond
            ((= after 1) 'harmonic)
            ((= after 2) 'harmonic-black)
            (else (error "Caret number must be 1 or 2"))
          )
        )
      )
    )
  )
)
% 通常の音符、harmonicsの関数終わり----------------------