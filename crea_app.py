import os
import sys
import shutil
import subprocess
import textwrap
import random
import string
import platform
from PIL import Image
# QUESTO SCRIPT È IL RISULTATO FINALE E FUNZIONANTE.
# È MULTIPIATTAFORMA (WINDOWS/LINUX/MAC).
# ESECUZIONE: python3 crea_app_finale.py <nome_cartella_web>

# --- CONTENUTO DEI FILE TEMPLATE ---

def get_settings_gradle():
    return "include ':app'\n"

def get_root_build_gradle():
    return textwrap.dedent("""
    buildscript {
        repositories {
            google()
            mavenCentral()
        }
        dependencies {
            classpath 'com.android.tools.build:gradle:8.2.2'
        }
    }

    allprojects {
        repositories {
            google()
            mavenCentral()
        }
    }
    """)

def get_app_build_gradle(package_name):
    return textwrap.dedent(f"""\
    import java.util.Properties
    import java.io.FileInputStream

    def keystorePropertiesFile = file("keystore.properties")
    def keystoreProperties = new Properties()
    if (keystorePropertiesFile.exists()) {{
        keystoreProperties.load(new FileInputStream(keystorePropertiesFile))
    }}

    apply plugin: 'com.android.application'

    android {{
        namespace '{package_name}'
        compileSdkVersion 33
        
        signingConfigs {{
            release {{
                if (keystorePropertiesFile.exists()) {{
                    storeFile file(keystoreProperties['storeFile'])
                    storePassword keystoreProperties['storePassword']
                    keyAlias keystoreProperties['keyAlias']
                    keyPassword keystoreProperties['keyPassword']
                }}
            }}
        }}

        defaultConfig {{
            applicationId "{package_name}"
            minSdkVersion 21
            targetSdkVersion 33
            versionCode 1
            versionName "1.0"
        }}
        
        buildTypes {{
            release {{
                minifyEnabled false
                proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
                signingConfig signingConfigs.release
            }}
        }}
    }}

    dependencies {{
        // No external dependencies needed for a simple WebView
    }}
    """)

def get_android_manifest(package_name, app_name):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">

    <uses-permission android:name="android.permission.INTERNET" />

    <application
        android:allowBackup="true"
        android:label="{app_name}"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher"
        android:supportsRtl="true"
        android:theme="@android:style/Theme.NoTitleBar"
        android:usesCleartextTraffic="true">
        <activity android:name=".MainActivity"
                  android:exported="true"
                  android:configChanges="orientation|screenSize">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
'''

def get_main_activity(package_name):
    return textwrap.dedent(f"""
    package {package_name};

    import android.app.Activity;
    import android.os.Bundle;
    import android.webkit.WebSettings;
    import android.webkit.WebView;
    import android.webkit.WebViewClient;
    import android.webkit.WebChromeClient;
    import android.view.KeyEvent;
    import android.view.View;
    import android.view.ViewGroup;
    import android.view.WindowManager;
    import android.widget.FrameLayout;

    public class MainActivity extends Activity {{

        private WebView myWebView;
        private View mCustomView;
        private WebChromeClient.CustomViewCallback mCustomViewCallback;
        private FrameLayout mFullscreenContainer;

        @Override
        protected void onCreate(Bundle savedInstanceState) {{
            super.onCreate(savedInstanceState);
            setContentView(R.layout.activity_main);

            myWebView = (WebView) findViewById(R.id.webview);

            WebSettings webSettings = myWebView.getSettings();
            webSettings.setJavaScriptEnabled(true);
            webSettings.setDomStorageEnabled(true);
            webSettings.setAllowFileAccess(true);
            webSettings.setAllowContentAccess(true);
            webSettings.setMediaPlaybackRequiresUserGesture(false);

            myWebView.setWebViewClient(new WebViewClient());
            
            myWebView.setWebChromeClient(new WebChromeClient() {{
                @Override
                public void onShowCustomView(View view, CustomViewCallback callback) {{
                    if (mCustomView != null) {{
                        onHideCustomView();
                        return;
                    }}
                    mCustomView = view;
                    mCustomViewCallback = callback;

                    // 1. Attiva la modalità immersiva (Nasconde tasti Android e Status Bar)
                    getWindow().getDecorView().setSystemUiVisibility(
                            View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                            | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                            | View.SYSTEM_UI_FLAG_FULLSCREEN
                            | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY);

                    // 2. Prepara il container per il video
                    ViewGroup rootView = (ViewGroup) getWindow().getDecorView();
                    mFullscreenContainer = new FrameLayout(MainActivity.this);
                    mFullscreenContainer.setBackgroundColor(0xFF000000); // Nero assoluto
                    
                    mFullscreenContainer.addView(view, new FrameLayout.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT));
                    
                    rootView.addView(mFullscreenContainer, new ViewGroup.LayoutParams(
                            ViewGroup.LayoutParams.MATCH_PARENT,
                            ViewGroup.LayoutParams.MATCH_PARENT));

                    myWebView.setVisibility(View.GONE);
                }}

                @Override
                public void onHideCustomView() {{
                    if (mCustomView == null) return;

                    // 1. Ripristina la visibilità dell'interfaccia Android normale
                    getWindow().getDecorView().setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE);

                    // 2. Rimuovi il video dal root layout
                    ViewGroup rootView = (ViewGroup) getWindow().getDecorView();
                    rootView.removeView(mFullscreenContainer);
                    mFullscreenContainer = null;
                    mCustomView = null;
                    mCustomViewCallback.onCustomViewHidden();
                    
                    // 3. Torna alla WebView
                    myWebView.setVisibility(View.VISIBLE);
                }}
            }});

            myWebView.loadUrl("file:///android_asset/index.html");
        }}

        @Override
        public boolean onKeyDown(int keyCode, KeyEvent event) {{
            // Se premo "Indietro" mentre il video è aperto, lo chiude
            if (keyCode == KeyEvent.KEYCODE_BACK && mCustomView != null) {{
                myWebView.getWebChromeClient().onHideCustomView();
                return true;
            }}
            // Altrimenti gestisce la cronologia della WebView
            if ((keyCode == KeyEvent.KEYCODE_BACK) && myWebView.canGoBack()) {{
                myWebView.goBack();
                return true;
            }}
            return super.onKeyDown(keyCode, event);
        }}
    }}
    """)
    
def get_layout(package_name):
    return f'''<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    tools:context="{package_name}.MainActivity">

    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />

</RelativeLayout>
'''

# ==============================
# ICON GENERATOR
# ==============================

def generate_icons(source_icon, res_path):
    sizes = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    try:
        img = Image.open(source_icon).convert("RGBA")

        for folder, size in sizes.items():
            out_dir = os.path.join(res_path, folder)
            os.makedirs(out_dir, exist_ok=True)
            out_img = img.resize((size, size), Image.LANCZOS)
            out_img.save(os.path.join(out_dir, "ic_launcher.png"), format="PNG")
        print(f"   - Icone generate da {source_icon}")
    except Exception as e:
        print(f"❌ ERRORE durante la generazione delle icone: {e}")
        print("   Verranno utilizzate icone di default (se disponibili)")
def get_gradle_wrapper_properties():
    return "distributionUrl=https://services.gradle.org/distributions/gradle-8.5-bin.zip\n"

def get_local_properties(sdk_path):
    # Usa forward slashes anche su Windows, Java lo gestisce correttamente
    return f"sdk.dir={sdk_path.replace('\\', '/')}\n"

def get_gradlew_unix_script():
    return "#!/usr/bin/env sh\nset -e\nDIR=$(cd \"$(dirname \"$0\")\" && pwd)\nexec java -cp \"$DIR/gradle/wrapper/gradle-wrapper.jar\" org.gradle.wrapper.GradleWrapperMain \"$@\"\n"

def get_gradlew_windows_script():
    return textwrap.dedent("""
    @if "%DEBUG%" == "" @echo off
    @rem ##########################################################################
    @rem
    @rem  Gradle startup script for Windows
    @rem
    @rem ##########################################################################
    @rem Set local scope for the variables with windows NT shell
    if "%OS%"=="Windows_NT" setlocal
    set DIRNAME=%~dp0
    if "%DIRNAME%" == "" set DIRNAME=.
    set APP_BASE_NAME=%~n0
    set APP_HOME=%DIRNAME%
    @rem Add default JVM options here. You can also use JAVA_OPTS and GRADLE_OPTS to pass JVM options to this script.
    set DEFAULT_JVM_OPTS="-Xmx64m" "-Xms64m"
    @rem Find java.exe
    if defined JAVA_HOME goto findJavaFromJavaHome
    set JAVA_EXE=java.exe
    %JAVA_EXE% -version >NUL 2>&1
    if "%ERRORLEVEL%" == "0" goto init
    echo.
    echo ERROR: JAVA_HOME is not set and no 'java' command could be found in your PATH.
    echo.
    echo Please set the JAVA_HOME variable in your environment to match the
    echo location of your Java installation.
    echo.
    goto end
    :findJavaFromJavaHome
    set JAVA_HOME=%JAVA_HOME:"=%
    set JAVA_EXE=%JAVA_HOME%\\bin\\java.exe
    if exist "%JAVA_EXE%" goto init
    echo.
    echo ERROR: JAVA_HOME is set to an invalid directory: %JAVA_HOME%
    echo.
    echo Please set the JAVA_HOME variable in your environment to match the
    echo location of your Java installation.
    echo.
    goto end
    :init
    @rem Get command-line arguments, handling Windowz variants
    if not "%OS%" == "Windows_NT" goto win9xME_args
    if "%@eval[2+2]" == "4" goto 4NT_args
    :win9xME_args
    @rem Slurp the command line arguments.
    set CMD_LINE_ARGS=
    set _SKIP=2
    :win9xME_args_slurp
    if "x%~1" == "x" goto execute
    set CMD_LINE_ARGS=%*
    goto execute
    :4NT_args
    @rem Get arguments from the 4NT Shell.
    set CMD_LINE_ARGS=%*
    :execute
    @rem Setup the command line
    set CLASSPATH=%APP_HOME%\\gradle\\wrapper\\gradle-wrapper.jar
    @rem Execute Gradle
    "%JAVA_EXE%" %DEFAULT_JVM_OPTS% %JAVA_OPTS% %GRADLE_OPTS% "-Dorg.gradle.appname=%APP_BASE_NAME%" -classpath "%CLASSPATH%" org.gradle.wrapper.GradleWrapperMain %CMD_LINE_ARGS%
    :end
    if "%OS%"=="Windows_NT" endlocal
    :omega
    """)
# --- FUNZIONI DELLO SCRIPT ---

def print_usage():
    print("Uso: python3 crea_app.py <nome_cartella_web> [percorso_icona]")
    print("Esempio 1: python3 crea_app.py miosito")
    print("Esempio 2: python3 crea_app.py miosito ./logo.png")
    print("\nNote:")
    print("- La cartella web deve contenere un file index.html")
    print("- L'icona può essere in formato PNG, JPG, SVG, etc.")
    print("- Se non viene fornita un'icona, l'app userà l'icona di default")

# ==============================
# MAIN SCRIPT
# ==============================

def main():
    is_windows = platform.system() == "Windows"

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    web_dir_name = sys.argv[1].rstrip('/\\')
    if not os.path.isdir(web_dir_name):
        print(f"❌ Errore: La cartella '{web_dir_name}' non esiste.")
        sys.exit(1)

    icon_path = None
    if len(sys.argv) >= 3:
        icon_path = sys.argv[2]
        if not os.path.exists(icon_path):
            print(f"❌ Avviso: Il file icona '{icon_path}' non esiste. Verrà utilizzata l'icona di default.")
            icon_path = None

    android_sdk_home = os.environ.get("ANDROID_HOME")
    if not android_sdk_home:
        print("❌ ERRORE: La variabile d'ambiente ANDROID_HOME non è impostata.")
        sys.exit(1)
        
    java_home = os.environ.get("JAVA_HOME")
    if not java_home:
        print("❌ ERRORE: La variabile d'ambiente JAVA_HOME non è impostata.")
        print("          È necessario impostare JAVA_HOME a un JDK versione 11 o superiore.")
        print("          Esempio (Linux/macOS): export JAVA_HOME=/path/to/jdk-11")
        print("          Esempio (Windows PowerShell): $env:JAVA_HOME='C:\\path\\to\\jdk-11'")
        sys.exit(1)
    # Potremmo aggiungere un controllo più robusto della versione Java qui,
    # ma per ora un semplice check di esistenza è sufficiente per guidare l'utente.

    app_name = os.path.basename(os.path.abspath(web_dir_name))
    package_name = f"com.{app_name.lower().replace(' ', '').replace('-', '_')}"
    project_dir = f"{app_name}_android_app"

    print(f"🚀 Inizio creazione app per '{app_name}' su sistema {platform.system()}")

    # 1. Pulisci e crea la struttura delle cartelle
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir)
    
    app_dir = os.path.join(project_dir, 'app')
    package_path = os.path.join(app_dir, 'src', 'main', 'java', *package_name.split('.'))
    assets_path = os.path.join(app_dir, 'src', 'main', 'assets')
    layout_path = os.path.join(app_dir, 'src', 'main', 'res', 'layout')
    res_path = os.path.join(app_dir, 'src', 'main', 'res')
    wrapper_path = os.path.join(project_dir, 'gradle', 'wrapper')
    
    for path in [package_path, assets_path, layout_path, wrapper_path, res_path]:
        os.makedirs(path, exist_ok=True)
    
    # 2. Scrivi tutti i file di configurazione
    print("   - Scrittura dei file di configurazione...")
    with open(os.path.join(project_dir, 'settings.gradle'), 'w') as f: f.write(get_settings_gradle())
    with open(os.path.join(project_dir, 'build.gradle'), 'w') as f: f.write(get_root_build_gradle())
    with open(os.path.join(app_dir, 'build.gradle'), 'w') as f: f.write(get_app_build_gradle(package_name))
    with open(os.path.join(wrapper_path, 'gradle-wrapper.properties'), 'w') as f: f.write(get_gradle_wrapper_properties())
    with open(os.path.join(project_dir, 'local.properties'), 'w') as f: f.write(get_local_properties(android_sdk_home))

    # 3. Scrivi i file sorgente dell'app
    with open(os.path.join(app_dir, 'src', 'main', 'AndroidManifest.xml'), 'w') as f: f.write(get_android_manifest(package_name, app_name))
    with open(os.path.join(package_path, 'MainActivity.java'), 'w') as f: f.write(get_main_activity(package_name))
    with open(os.path.join(layout_path, 'activity_main.xml'), 'w') as f: f.write(get_layout(package_name))

    if icon_path and os.path.exists(icon_path):
        generate_icons(icon_path, res_path)
    else:
        print("   - Icona non fornita, verrà utilizzata l'icona di default di Android")

    print("   - Copia dei file web...")
    shutil.copytree(web_dir_name, assets_path, dirs_exist_ok=True)

    # Prepara l'ambiente per le chiamate subprocess in modo che usino il JAVA_HOME corretto
    env_for_gradle = os.environ.copy()
    if java_home: # Se JAVA_HOME è impostato, lo prepende a PATH per i subprocessi
        env_for_gradle["PATH"] = os.path.join(java_home, "bin") + os.pathsep + env_for_gradle["PATH"]

    # ... (all subprocess.run calls will now use this env_for_gradle) ...

    # 5. Genera chiave di firma
    print("   - Generazione della chiave di firma...")
    keystore_password = "aimods2025" # Password semplice per automazione
    keystore_filename = f"{app_name}.keystore"
    key_alias = f"{app_name}_alias"
    
    keytool_command = [
        "keytool", "-genkey", "-v",
        "-keystore", keystore_filename,
        "-alias", key_alias,
        "-keyalg", "RSA", "-keysize", "2048",
        "-validity", "10000",
        "-storepass", keystore_password,
        "-keypass", keystore_password,
        "-dname", f"CN={package_name}, OU=Web2App, O=Web2App, L=Unknown, S=Unknown, C=XX"
    ]
    try:
        subprocess.run(keytool_command, cwd=app_dir, check=True, capture_output=True, text=True, shell=is_windows, env=env_for_gradle)
        props_content = (f"storePassword={keystore_password}\n"
                         f"keyPassword={keystore_password}\n"
                         f"keyAlias={key_alias}\n"
                         f"storeFile={keystore_filename}\n")
        with open(os.path.join(app_dir, 'keystore.properties'), 'w') as f: f.write(props_content)
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"❌ ERRORE con keytool: {e}. Assicurati che 'keytool' del JDK sia nel PATH.")
        if isinstance(e, subprocess.CalledProcessError): print(e.stderr)
        sys.exit(1)

    # 6. Prepara il Gradle Wrapper
    print("   - Preparazione del Gradle Wrapper...")
    if is_windows:
        gradlew_path = os.path.join(project_dir, 'gradlew.bat')
        with open(gradlew_path, 'w', encoding='utf-8') as f: f.write(get_gradlew_windows_script())
        gradlew_executable = 'gradlew.bat'
    else: # Linux/macOS
        gradlew_path = os.path.join(project_dir, 'gradlew')
        with open(gradlew_path, 'w', encoding='utf-8') as f: f.write(get_gradlew_unix_script())
        os.chmod(gradlew_path, 0o755)
        gradlew_executable = './gradlew'

    try:
        import urllib.request
        wrapper_jar_url = "https://github.com/gradle/gradle/raw/v8.5.0/gradle/wrapper/gradle-wrapper.jar"
        print("     - Download di gradle-wrapper.jar...")
        with urllib.request.urlopen(wrapper_jar_url) as response, open(os.path.join(wrapper_path, 'gradle-wrapper.jar'), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
    except Exception as e:
        print(f"❌ ERRORE durante il download del wrapper: {e}")
        sys.exit(1)

    # 7. Esegui la build
    print("   - Avvio di Gradle per la compilazione della RELEASE...")
    try:
        subprocess.run([gradlew_executable, ':app:assembleRelease'], cwd=project_dir, check=True, text=True, shell=is_windows, env=env_for_gradle)
        print("✅ Build completata con successo!")
    except subprocess.CalledProcessError as e:
        print("❌ ERRORE DURANTE LA BUILD DI GRADLE!")
        print(e.stderr)
        sys.exit(1)

    # DIAGNOSTICA: Elenca il contenuto della directory di output dell'APK
    apk_output_dir_actual = os.path.join(app_dir, 'build', 'outputs', 'apk', 'release')
    print(f"   - Contenuto della directory di output: {apk_output_dir_actual}")
    if os.path.exists(apk_output_dir_actual):
        if is_windows:
            subprocess.run(['cmd', '/c', 'dir', apk_output_dir_actual], check=True, text=True)
        else:
            subprocess.run(['ls', '-l', apk_output_dir_actual], check=True, text=True)
    else:
        print(f"     (La directory di output non esiste: {apk_output_dir_actual})")

    # 8. Sposta l'APK finale
    print("   - Spostamento dell'APK finale...")
    apk_output_dir = "apk_generati"
    os.makedirs(apk_output_dir, exist_ok=True)
    apk_final_name = f"{app_name}.apk"
    apk_final_path = os.path.join(apk_output_dir, apk_final_name)

    # Prova prima il nome standard, poi il fallback "unsigned"
    candidates = [
        os.path.join(app_dir, 'build', 'outputs', 'apk', 'release', 'app-release.apk'),
        os.path.join(app_dir, 'build', 'outputs', 'apk', 'release', 'app-release-unsigned.apk')
    ]

    found_apk = False
    for candidate_path in candidates:
        if os.path.exists(candidate_path):
            shutil.move(candidate_path, apk_final_path)
            found_apk = True
            print(f"   - APK trovato: {candidate_path}")
            break
    
    if not found_apk:
        print(f"❌ ERRORE: Nessun APK di release trovato nei percorsi attesi.")
        print("   Percorsi cercati:")
        for p in candidates: print(f"     - {p}")
        sys.exit(1)

    # 9. Pulizia
    print(f"   - Pulizia della cartella di progetto '{project_dir}'...")
    shutil.rmtree(project_dir)

    print(f"\n🎉🎉🎉 FATTO! L'APK di RELEASE si trova qui: {os.path.abspath(apk_final_path)}")

if __name__ == '__main__':
    main()