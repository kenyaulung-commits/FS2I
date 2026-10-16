export GRADLE_USER_HOME=/tmp/gradle_home
mkdir -p /tmp/gradle_home
export GRADLE_OPTS="-Dorg.gradle.jvmargs='-Xmx1536m -XX:MaxMetaspaceSize=512m' -Dorg.gradle.daemon=false -Dorg.gradle.parallel=false -Dorg.gradle.workers.max=1"
export ANDROID_HOME=/home/codespace/Android/sdk
export ANDROID_SDK_ROOT=/home/codespace/Android/sdk
export PATH=$PATH:$ANDROID_HOME/cmdline-tools/latest/bin:$ANDROID_HOME/platform-tools
