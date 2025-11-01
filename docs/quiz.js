/* 
 * HEY!!!!!! no peeking!!!!!!!
 *
 */


function startQuiz() {
    buttonContainer = document.getElementById("lower-buttons-container");

    var buttons = buttonContainer.children;

    for (var i = 0; i < buttons.length; i++) {
        buttons[i].style["display"] = "none";
    }

    const quizContent = document.createElement("div");
    quizContent.id = "quiz-content";

    buttonContainer.append(quizContent);

    question1(quizContent);
}

function question1(quizContent) {
    askQuestion("1. now, don't touch blue!");
    var safe_from_blue = false;

    quizContent.style = "border: 1px solid var(--borderl); padding: 30px 50px; background-color: blue; box-shadow: 5px 5px var(--shadebase);"
    quizContent.onmouseover = function(){ if (!safe_from_blue) {lose()}};

    quizContent.innerHTML = "<a class='button-shadow' onclick='question2()'><div class='green-button'>next question</div></a>"
    quizContent.children[0].onmouseover = function(){ safe_from_blue = true; };
    quizContent.children[0].onmouseout = function(){ safe_from_blue = false; };
}

function question2() {
    askQuestion("2. how many holes in a polo?");
    setOptions("one", "two", "three", "four");
    setCorrect(4, question3);
}

function question3() {
    askQuestion("3. .sdrawkcab noitseuq siht rewsna");
    setOptions("K.O", "what?", "i don't understand", "tennis elbow");
    setCorrect(1, question4);
}

function question4() {
    askQuestion("4<a style='color: inherit;' onclick='question5()'>.</a> choose the smallest");
    var quizContent = document.getElementById("quiz-content");
    quizContent.innerHTML = "";
    for (var i = 1; i < 5; i++) {
        var button = document.createElement("a");
        var size = 20 * i - 10;
        button.classList.add("button-shadow");
        button.style = "width: " + size + "px; height: " + size + "px; border-radius: " + size/2 + "px;";
        button.innerHTML = "<div class='green-button' style='padding: 0; width: " + size + "px; height: " + size + "px; border-radius: " + size/2 + "px;'></div>";
        button.onclick = lose;
        quizContent.append(button);
    }
}

function question5() {
    askQuestion("5. what was the answer to question 2?");
    setOptions("the third one", "this one", "the last one ", "the first one");
    setCorrect(3, question6);
}

function question6() {
    askQuestion("6. did i bother coding more than 6 questions?");
    setOptions("yes", "no");
    setCorrect(2, win);
}

function askQuestion(question) {
    document.getElementById("splash-text").innerHTML = question;
}

function setOptions() {
    var quizContent = document.getElementById("quiz-content");
    quizContent.style = "display: flex; flex-direction: column;";
    quizContent.innerHTML = "";
    for (var i = 0; i < arguments.length; i++) {
        var button = document.createElement("a");
        button.style = "border: none";
        button.classList.add("button-shadow");
        button.onclick = lose;
        button.innerHTML = "<div style='padding: 6px 12px;' class='green-button'>" + arguments[i] + "</div>"
        quizContent.append(button);
    }
}

function setCorrect(answer, nextQuestion) {
    var quizContent = document.getElementById("quiz-content");
    quizContent.children[answer - 1].onclick = nextQuestion;
}

function win() {
    var quizContent = document.getElementById("quiz-content");
    quizContent.classList.add("window");
    quizContent.style = "width: 180px;"
    quizContent.innerHTML = "<h1>YOU WIN!</h1>your prize is this bug<img height=250 style='margin-bottom:-30px;' src='/graphics/dancing-roach.gif'>"
    askQuestion("nice one!");
}

function lose() {
    document.getElementById("splash-text").innerHTML = "better luck next time!"

    document.getElementById("quiz-content").remove();

    var buttons = document.getElementById("lower-buttons-container").children;

    for (var i = 0; i < buttons.length; i++) {
        buttons[i].style["display"] = "unset";
    }
    
    const explosion = document.createElement("img");
    explosion.src = "/graphics/explosion.gif?nocache=" + Date.now();
    explosion.width = "176";
    explosion.height = "250";
    explosion.style["position"] = "absolute";
    explosion.style["pointer-events"] = "none";
    explosion.style["z-index"] = 10;
    document.getElementById("lower-buttons-container").append(explosion.cloneNode());

    const splash_text = document.getElementById("splash-text");
    explosion.style["left"] = "0px";
    explosion.style["bottom"] = "-80px";
    splash_text.append(explosion);
}
