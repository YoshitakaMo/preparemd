# PrepareMD

Toolkit to prepare AMBER files for MD simulations.

## What is PrepareMD?

チュートリアルに沿って、入力とするpdbファイルからAMBERでのMDシミュレーション実行のために必要なファイルを自動生成するPythonスクリプト（※Gromacs用は現在開発中）。現在はmmcifをインプットとする場合には未対応。

## 特長

このパッケージの特長

- チュートリアルに沿ってトポロジーファイルを含むディレクトリ`top`とMDの実行ファイルを含むディレクトリ`amber/{minimize,heat,pr}`を自動的に生成する。
- MDシミュレーションをminimize, heat, prと一気に実行可能な`totalrun.sh`をproduction runのディレクトリ`amber/pr`内に自動生成する。
- production runのディレクトリ`amber/pr`内に生成するサブディレクトリの数を引数`--num_mddir`と`--ns_per_box`調節可能。
- **SS結合のペアを入力pdbファイルの構造情報から推定して自動的に適切に設定する**。
- 上に加え、SS結合ペア情報を外部ファイル`sslink`から上書き可能。AlphaFoldで出てきた構造では想定と異なるSS結合になっている場合が時々あるため、このケースに対応した機能である。
- ボックスサイズを引数`--boxsize`から指定可能。
- ボックスサイズに応じてイオン濃度を引数`--ion_conc`から調節可能。
- MDトラジェクトリを解析するための`trajfix.in`を自動生成。

## インストール方法

以下のソフトウェアが必要。

- お使いのPC/Macに[AMBER24またはambertools25以上がインストール](https://qiita.com/Ag_smith/items/9526142858f8ea5248c1)されていること
- Python3（> 3.10）以上で、Pythonライブラリの依存を解決しておく。

macOSを使用している場合、Homebrewで`brew install python@3.13`を使用してpython3.13をインストールするのが便利。

> [!NOTE]
>
> If you are using python3.13, create and activate venv at first
> `/path/to/workingdirectory` is your working directory.
>
> ```bash
> mkdir -p /path/to/workingdirectory ; cd /path/to/workingdirectory
> python3.13 -m venv .venv
> source .venv/bin/activate
> ```

```bash
# install from GitHub
python3 -m pip install git+https://github.com/YoshitakaMo/preparemd.git
# upgrade
python3 -m pip uninstall preparemd -y && python3 -m pip install --upgrade git+https://github.com/YoshitakaMo/preparemd.git
```

### 開発者向け

- 現在は[uvを使ったパッケージ管理](https://qiita.com/Ag_smith/items/bd8b67d4e0c4255ecd09)を利用しているので、そちらをインストールしておく。

```bash
cd /path/to/your/workingdirectory
git clone https://github.com/YoshitakaMo/preparemd.git
cd preparemd
uv self update
uv sync
```

## How To Use

仕様上、指定可能な引数が多く設定されていますので1つ1つ確認していってください。

```bash
. /path/to/workingdirectory/.venv/bin/activate  # venvを使っている場合は有効化
preparemd \
    --file /path/to/your/foo.pdb \
    --distdir /path/to/your/targetdirectory \
    --fftype "ff19SB" \
    --num_mddir 3 \
    --ns_per_mddir 50 \
    --boxsize "120 120 120" \
    --ion_conc 150 \
    --strip ":793-807,864-878" \
    --sslink /path/to/pre_sslink \
    --rotate "rotate z 45" \
    --machineenv foodin \
    --trajprefix foobar \
    --frcmod "/path/to/frcmod.lig1" "/path/to/frcmod.lig2" \
    --prep "/path/to/prep1.prep" "/path/to/prep2.prep" \
    --mol2 "ACA = loadMol2 Acetyl_CoA.mol2" \
    --mol2 "DON = loadMol2 DON.mol2"
```

- `--file`は入力とするPDB**ファイルパス**。**実行に必須**。**AlphaFoldで出力されてきたPDBフォーマットにも対応している**。
- `--distdir`は出力先の**ディレクトリ名**。**実行に必須**。この中にトポロジーファイルを含む`top`ディレクトリとMDの実行ファイル`amber/{minimize,heat,pr}`を生成する。
- `--fftype`は`ff14SB`と`ff19SB`のいずれかを指定する。力場の指定。デフォルトは最新の`ff19SB`だが、以前の結果と合わせる場合には`ff14SB`を使うと良い。
- `--num_mddir`は`amber/pr`ディレクトリ内に指定した数分だけのprodution run実行サブディレクトリを生成する。ナンバリングは3桁になるよう0埋めされる（例：`001`, `002`, `003`,...)。デフォルトは`3`。
- `--ns_per_mddir`は各production runサブディレクトリあたりで実行されるMDシミュレーションの上限時間(ns)。デフォルトは`50`。
- `--boxsize`はMDシミュレーションを実行するときの周期境界ボックスのサイズ。 **必ず`"x y z"`のように3つ組の整数値を入れる**。指定しない場合は、溶質の大きさに応じてその周囲10Åを余分にとった大きさになる。異方性の大きい溶質の場合のときなどは、立方体になるよう明示的に指定したほうが良い。
- `--ion_conc`は周期境界ボックス内に配置するイオンの濃度(mM)を指定する。デフォルトは150 mM。
- `--strip`は**AMBER MASK文法**でMDシミュレーションに含めない領域を指定する。例えばAlphaFoldで予測された構造にシグナルペプチドなどの余分な長い領域がついている場合があって、それを除いてシミュレーションさせたいときなどに使う。**仕様上、この残基ナンバリングは入力とするpdbファイルのN末端からの通し番号となることに注意**。言い換えれば、leapを通った後に1番から再ナンバリングされたときの番号である。例えば`--strip=":793-807,864-878"`を指定したとすると、入力pdbファイルのN末端から数えて793-807と864-878番目の残基を取り除いてからleapを通してMDのインプットファイルを生成することになる。
- `--sslink`は正しいSS結合を形成するCYS残基の残基番号ペアの情報を含むsslinkファイルへのパスを指定する。フォーマットは後述。このオプションが指定されない場合は、入力とするpdbファイルの構造から自動的に適切と思われるSS結合情報を取得し、SS結合を形成する。
- `--rotate`を指定すると、AmberToolsの`cpptraj`内で使われるrotateコマンドを使って指定した軸回りに入力pdbの構造を回転させてからleap処理を実行する。例えば`--rotate "rotate z 45"`はz軸回りに45°回転させるというもの。
- `--machineenv`は計算機環境を指定する。これはMDを動かす`run.sh`のヘッダー部分を変化させる。現在のところ`yayoi`, `foodin`, `tsubame`, `flow`を用意している。デフォルトは`foodin`。
- `--trajprefix`は`trajfix.in`の中で出力される予定の`init.pdb`と`traj.trr`のファイルの先頭につけるプレフィックス文字。
- `--frcmod`, `--prep`はそれぞれ追加の力場パラメータ、小分子パラメータ（prep形式）へのファイルパスを指定。**スペース区切りで複数入力可能。これらのファイルはすべて`top`ディレクトリにコピーされる。**
- `--mol2`ファイルはmol2形式の追加の小分子パラメータへのファイルパス。これはAMBERの`leap.in`に書く方法と同じ。**複数回指定可能。**
- `--norun_leap`を指定すると、`leap.parm7`や`leap.rst7`ファイルを生成しないがその他のファイルを生成する。leap処理を機械的に行うことが難しいために、手動でleap部分だけ調整しておきたいという人向け。

sslinkファイルのフォーマットは以下の通り。これはAmberToolsの`pdb4amber`コマンドで生成されるフォーマットと同じ。各番号は入力とするpdbファイルのN末端から通して数えたときの残基番号。またこの残基番号がCYSでない場合はエラーとなる。

```:sslink
262 274
268 282
284 305
313 351
343 368
347 353
```

## Customize

`amber/md`または`amber/top`にあるファイルが出力テンプレートとなっているので、それらを適当にいじってください。
