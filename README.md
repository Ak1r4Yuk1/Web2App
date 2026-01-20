# Web2App: Crea App Android WebView dai tuoi Siti Web Locali

[![GitHub license](https://img.shields.io/github/license/Naereen/StrapDown.js.svg)](https://github.com/your-username/Web2App/blob/main/LICENSE)
[![Python version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/downloads/)
[![Android SDK](https://img.shields.io/badge/Android%20SDK-min%2033-green)](https://developer.android.com/studio/releases/platforms)
[![JDK](https://img.shields.io/badge/JDK-11%2B-orange)](https://www.oracle.com/java/technologies/javase/jdk-prior-releases.html)

## Descrizione

Il progetto **Web2App** fornisce uno script Python semplice ma potente (`crea_app.py`) per convertire le tue directory contenenti file web (HTML, CSS, JavaScript, immagini, ecc.) in un'applicazione Android nativa basata su `WebView`. Questo ti permette di trasformare rapidamente prototipi web o siti web statici in app Android installabili, con un minimo sforzo.

Lo script automatizza l'intera pipeline di build Android, inclusa la configurazione di Gradle, la generazione della chiave di firma e la compilazione dell'APK di release. È progettato per essere multipiattaforma, funzionando sia su sistemi Linux/macOS che Windows.

## Caratteristiche

*   **Generazione Automatica**: Crea uno scheletro completo di progetto Android Gradle.
*   **WebView Integrata**: La tua app carica il file `index.html` dalla directory specificata.
*   **APK di Release Firmato**: Genera automaticamente una chiave di firma e compila un APK di release pronto per l'installazione.
*   **Multipiattaforma**: Funziona su Linux, macOS e Windows.
*   **Facile da Usare**: Richiede solo un comando dopo una breve configurazione dell'ambiente.
*   **Custom icon**: Puoi selezionare la tua icona per la app

## Prerequisiti

Per utilizzare questo script, il tuo sistema deve avere installati e configurati i seguenti componenti:

1.  **Python 3.x**: Per eseguire lo script.
2.  **Java Development Kit (JDK) 11 o superiore**: Necessario per la compilazione del codice Android e l'esecuzione di Gradle.
3.  **Android SDK**: Il kit di sviluppo Android, che include gli strumenti da riga di comando.
4.  **Connessione Internet**: Necessaria per il download delle dipendenze di Gradle.

### Configurazione delle Variabili d'Ambiente

È **cruciale** impostare correttamente le seguenti variabili d'ambiente:

#### `JAVA_HOME` (JDK 11+ richiesto)

`JAVA_HOME` deve puntare alla directory radice della tua installazione JDK 11 o superiore.

*   **Linux/macOS (Bash/Zsh):**
    ```bash
    export JAVA_HOME=/path/to/your/jdk-11 # Esempio: /usr/lib/jvm/java-11-openjdk/
    export PATH=$JAVA_HOME/bin:$PATH
    ```
*   **Windows (PowerShell):**
    ```powershell
    $env:JAVA_HOME="C:\Path\to\your\jdk-11" # Esempio: C:\Program Files\Java\jdk-11
    $env:Path="$env:JAVA_HOME\bin;$env:Path"
    ```
*   **Windows (CMD):**
    ```cmd
    set JAVA_HOME="C:\Path\to\your\jdk-11"
    set Path="%JAVA_HOME%\bin;%Path%"
    ```
    **Importante su Windows**: Assicurati che il percorso `%JAVA_HOME%in` sia all'inizio della tua variabile `Path` di sistema per evitare conflitti con vecchie installazioni Java.

#### `ANDROID_HOME`

`ANDROID_HOME` deve puntare alla directory radice della tua installazione dell'Android SDK.

*   **Linux/macOS (Bash/Zsh):**
    ```bash
    export ANDROID_HOME=/path/to/your/android/sdk # Esempio: ~/Android/Sdk
    export PATH=$ANDROID_HOME/cmdline-tools/latest/bin:$PATH # Per i tool più recenti
    ```
*   **Windows (PowerShell):**
    ```powershell
    $env:ANDROID_HOME="C:\Path\to\your\Android\Sdk" # Esempio: C:\Users\YourUser\AppData\Local\Android\Sdk
    $env:Path="$env:ANDROID_HOME\cmdline-tools\latest\bin;$env:Path"
    ```
*   **Windows (CMD):**
    ```cmd
    set ANDROID_HOME="C:\Path\to\your\Android\Sdk"
    set Path="%ANDROID_HOME%\cmdline-tools\latest\bin;%Path%"
    ```

## Come Usare

1.  **Clona il Repository:**
    ```bash
    git clone https://github.com/your-username/Web2App.git
    cd Web2App
    ```

2.  **Prepara la tua Cartella Web:**
    Crea una cartella nella stessa directory dello script `crea_app.py` che contenga tutti i tuoi file web (HTML, CSS, JS, immagini, ecc.). Questa cartella **deve contenere un file `index.html`** nella sua radice.

    Esempio:
    ```
    Web2App/
    ├── crea_app.py
    └── IlMioSitoWeb/
        ├── index.html
        ├── css/
        └── js/
    ```

3.  **Esegui lo Script:**
    Apri un terminale nella directory `Web2App/` ed esegui lo script, passando il nome della tua cartella web come argomento:

    ```bash
    python3 crea_app.py IlMioSitoWeb
    ```
    Se vuoi una tua icona personalizzata:
    
    ```bash
    python3 crea_app.py IlMioSitoWeb tuaicona.png
    ```
    
    Sostituisci `IlMioSitoWeb` con il nome reale della tua cartella.

4.  **Trova il tuo APK:**
    Al completamento, lo script creerà una nuova directory `apk_generati/` nella directory `Web2App/`. All'interno troverai il tuo APK di release firmato, nominato come `IlMioSitoWeb.apk` (o il nome della cartella che hai fornito).

    ```
    Web2App/
    ├── crea_app.py
    ├── IlMioSitoWeb/
    └── apk_generati/
        └── IlMioSitoWeb.apk
    ```

5.  **Installa l'APK (Opzionale):**
    Puoi installare l'APK sul tuo dispositivo Android utilizzando `adb` (Android Debug Bridge):
    ```bash
    adb install apk_generati/IlMioSitoWeb.apk
    ```

## Personalizzazione (Avanzato)

*   **Nome della App, Package Name, ecc.**: I valori di default vengono ricavati dal nome della tua cartella web. Per personalizzarli, puoi modificare lo script `crea_app.py` prima di eseguirlo.
*   **Password Keystore**: Per motivi di automazione, la chiave di firma viene generata con password predefinite (`password123`). Per una vera app di produzione, dovresti usare password sicure e un keystore gestito manualmente.
*   **Tema/NoActionBar**: Il tema `NoActionBar` è già impostato nel `styles.xml` generato e applicato al manifest. Se desideri modificarlo, puoi intervenire sui template `get_styles_xml()` e `get_android_manifest()` all'interno di `crea_app.py`.

## Troubleshooting

*   **`JAVA_HOME` / `ANDROID_HOME` Errors**: Assicurati che le variabili d'ambiente siano impostate correttamente e puntino a installazioni valide.
*   **`Unsupported class file major version XX`**: Questo indica un conflitto di versione Java. La tua `JAVA_HOME` deve puntare a un JDK compatibile (JDK 11+ per le configurazioni correnti). Riprova a pulire la cache di Gradle (`Remove-Item -Recurse -Force $HOME\.gradle\caches` su PowerShell o `rmdir /s /q %USERPROFILE%\.gradle\caches` su CMD, oppure `rm -rf ~/.gradle/caches` su Linux). Assicurati anche che il tuo `PATH` di sistema non abbia voci Java più vecchie che hanno la precedenza.
*   **Gradle Daemon Issues**: Se incontri problemi persistenti legati a Gradle, prova a fermare tutti i daemon:
    ```bash
    # Da qualsiasi progetto Gradle o dove c'è un gradlew
    ./gradlew --stop # Linux/macOS
    .\gradlew --stop # Windows
    ```
*   **`HTTP Error 404` sul download del wrapper**: Se il download del `gradle-wrapper.jar` fallisce con un 404, significa che l'URL nel mio script non è più valido. In questo caso, lo script cercherà di scaricare l'intero Gradle Distribution ZIP (`gradle-8.5-bin.zip`), estrarre il `gradle-wrapper.jar` da lì e usarlo.

---

**Licenza**: Questo progetto è distribuito sotto licenza MIT.
