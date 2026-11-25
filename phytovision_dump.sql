--
-- PostgreSQL database dump
--

\restrict GN4kMzGwoqgyS4sU13WQBYFnxFC8jsOMzMsPOWSrWF28Jky3DebLJTb1jnxGHJy

-- Dumped from database version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)
-- Dumped by pg_dump version 16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.plants DROP CONSTRAINT IF EXISTS plants_genus_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plants DROP CONSTRAINT IF EXISTS plants_category_id_fkey;
ALTER TABLE IF EXISTS ONLY public.plant_care DROP CONSTRAINT IF EXISTS plant_care_plant_id_fkey;
DROP INDEX IF EXISTS public.idx_plants_genus;
DROP INDEX IF EXISTS public.idx_plants_category;
ALTER TABLE IF EXISTS ONLY public.plants DROP CONSTRAINT IF EXISTS plants_pkey;
ALTER TABLE IF EXISTS ONLY public.plants DROP CONSTRAINT IF EXISTS plants_class_id_key;
ALTER TABLE IF EXISTS ONLY public.plant_care DROP CONSTRAINT IF EXISTS plant_care_pkey;
ALTER TABLE IF EXISTS ONLY public.genera DROP CONSTRAINT IF EXISTS genera_pkey;
ALTER TABLE IF EXISTS ONLY public.genera DROP CONSTRAINT IF EXISTS genera_name_lat_key;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS categories_pkey;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS categories_name_ru_key;
ALTER TABLE IF EXISTS public.plants ALTER COLUMN plant_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.genera ALTER COLUMN genus_id DROP DEFAULT;
ALTER TABLE IF EXISTS public.categories ALTER COLUMN category_id DROP DEFAULT;
DROP VIEW IF EXISTS public.v_plant_info;
DROP SEQUENCE IF EXISTS public.plants_plant_id_seq;
DROP TABLE IF EXISTS public.plants;
DROP TABLE IF EXISTS public.plant_care;
DROP SEQUENCE IF EXISTS public.genera_genus_id_seq;
DROP TABLE IF EXISTS public.genera;
DROP SEQUENCE IF EXISTS public.categories_category_id_seq;
DROP TABLE IF EXISTS public.categories;
SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    category_id integer NOT NULL,
    name_ru character varying(64) NOT NULL
);


--
-- Name: categories_category_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.categories_category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: categories_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.categories_category_id_seq OWNED BY public.categories.category_id;


--
-- Name: genera; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.genera (
    genus_id integer NOT NULL,
    name_lat character varying(64) NOT NULL,
    name_ru character varying(128) NOT NULL,
    care_summary text
);


--
-- Name: genera_genus_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.genera_genus_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: genera_genus_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.genera_genus_id_seq OWNED BY public.genera.genus_id;


--
-- Name: plant_care; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plant_care (
    plant_id integer NOT NULL,
    summary text NOT NULL,
    light text NOT NULL,
    watering text NOT NULL,
    temperature text NOT NULL,
    feeding text NOT NULL,
    tips text NOT NULL
);


--
-- Name: plants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.plants (
    plant_id integer NOT NULL,
    class_id character varying(96) NOT NULL,
    name_lat character varying(128) NOT NULL,
    name_ru character varying(160) NOT NULL,
    genus_id integer NOT NULL,
    category_id integer NOT NULL,
    taxon_rank character varying(8) NOT NULL,
    CONSTRAINT plants_taxon_rank_check CHECK (((taxon_rank)::text = ANY ((ARRAY['species'::character varying, 'genus'::character varying])::text[])))
);


--
-- Name: plants_plant_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE public.plants_plant_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: plants_plant_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE public.plants_plant_id_seq OWNED BY public.plants.plant_id;


--
-- Name: v_plant_info; Type: VIEW; Schema: public; Owner: -
--

CREATE VIEW public.v_plant_info AS
 SELECT p.class_id,
    p.name_ru,
    p.name_lat,
    g.name_ru AS genus_ru,
    g.name_lat AS genus_lat,
    c.name_ru AS category_ru,
    p.taxon_rank,
    pc.summary,
    pc.light,
    pc.watering,
    pc.temperature,
    pc.feeding,
    pc.tips
   FROM (((public.plants p
     JOIN public.genera g ON ((g.genus_id = p.genus_id)))
     JOIN public.categories c ON ((c.category_id = p.category_id)))
     JOIN public.plant_care pc ON ((pc.plant_id = p.plant_id)));


--
-- Name: categories category_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories ALTER COLUMN category_id SET DEFAULT nextval('public.categories_category_id_seq'::regclass);


--
-- Name: genera genus_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.genera ALTER COLUMN genus_id SET DEFAULT nextval('public.genera_genus_id_seq'::regclass);


--
-- Name: plants plant_id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plants ALTER COLUMN plant_id SET DEFAULT nextval('public.plants_plant_id_seq'::regclass);


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (category_id, name_ru) FROM stdin;
1	Комнатные растения
2	Дача и огород
3	Сельское хозяйство
\.


--
-- Data for Name: genera; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.genera (genus_id, name_lat, name_ru, care_summary) FROM stdin;
1	Ficus	Фикус	Фикусы любят яркий рассеянный свет, постоянное место без сквозняков и умеренный полив после подсыхания верхнего слоя почвы. Листья периодически протирайте от пыли, зимой поливайте реже. Вид различается по листу: у каучуконосного листья крупные глянцевые, у Бенджамина мелкие заострённые, у лировидного крупные волнистые скрипкообразные.
2	Aloe	Алоэ	Алоэ — суккуленты: яркий свет, редкий полив только после полного просыхания грунта, рыхлый дренированный субстрат и прохладная зимовка. Основная причина гибели — переувлажнение.
3	Dracaena	Драцена	Драцены, включая сансевиерию, неприхотливы: рассеянный свет или полутень, умеренный полив после подсыхания верхнего слоя грунта (сансевиерию поливают заметно реже), защита от сквозняков и от застоя воды.
4	Pelargonium	Пеларгония (герань)	Пеларгонии любят много света, умеренный полив без застоя воды, прохладную зимовку и весеннюю обрезку. Листья не опрыскивают.
5	Solanum	Паслён	Паслёновые культуры (томат, картофель, баклажан) теплолюбивы: нужны солнце, регулярный полив под корень, подкормки и севооборот. Общая угроза — фитофтороз, поэтому не загущайте посадки и проветривайте теплицу.
6	Allium	Лук	Луковые (лук, чеснок) предпочитают солнечное место и рыхлую плодородную почву, умеренный полив с прекращением за 2–4 недели до уборки. Соблюдайте севооборот.
7	Prunus	Слива и вишня	Косточковые (вишня, слива) любят солнечное место, защищённое от ветра, нейтральную почву, полив в засуху и санитарную обрезку. Для урожая подбирайте опылители.
8	Brassica	Капуста	Капустные (капуста, рапс) — прохладолюбивые культуры: солнце, влажная плодородная почва, обильный полив, защита от крестоцветной блошки и севооборот.
9	Chlorophytum	Хлорофитум	\N
10	Spathiphyllum	Спатифиллум	\N
11	Zamioculcas	Замиокулькас	\N
12	Monstera	Монстера	\N
13	Epipremnum	Эпипремнум	\N
14	Crassula	Толстянка	\N
15	Kalanchoe	Каланхоэ	\N
16	Hibiscus	Гибискус	\N
17	Phalaenopsis	Фаленопсис	\N
18	Schlumbergera	Шлюмбергера (декабрист)	\N
19	Saintpaulia	Сенполия (узамбарская фиалка)	\N
20	Cucumis	Огурец	\N
21	Cucurbita	Тыква	\N
22	Capsicum	Перец	\N
23	Daucus	Морковь	\N
24	Anethum	Укроп	\N
25	Fragaria	Земляника и клубника	\N
26	Rubus	Малина	\N
27	Ribes	Смородина	\N
28	Malus	Яблоня	\N
29	Rosa	Роза	\N
30	Tulipa	Тюльпан	\N
31	Triticum	Пшеница	\N
32	Hordeum	Ячмень	\N
33	Secale	Рожь	\N
34	Avena	Овёс	\N
35	Zea	Кукуруза	\N
36	Helianthus	Подсолнечник	\N
37	Glycine	Соя	\N
38	Beta	Свёкла	\N
39	Fagopyrum	Гречиха	\N
40	Pisum	Горох	\N
\.


--
-- Data for Name: plant_care; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plant_care (plant_id, summary, light, watering, temperature, feeding, tips) FROM stdin;
1	Неприхотливое декоративно-лиственное растение с крупными глянцевыми листьями.	Яркий рассеянный свет, допустима лёгкая полутень.	Умеренно, когда верхний слой почвы подсохнет на 2–3 см; зимой реже.	18–25 °C; зимой не ниже 12–15 °C.	С апреля по сентябрь раз в 2–3 недели удобрением для декоративно-лиственных.	Протирайте листья влажной тканью, не переставляйте без нужды. Млечный сок может раздражать кожу.
2	Деревце с мелкими глянцевыми листьями; чувствительно к смене места и сквознякам.	Яркий рассеянный свет без жёсткого прямого солнца.	Умеренно, после подсыхания верхнего слоя; не допускайте застоя воды.	18–25 °C; зимой не ниже 15 °C.	С весны до осени раз в 2–3 недели.	Сбрасывает листья при сквозняках, перестановке и пересыхании кома.
3	Крупные волнистые листья скрипичной формы; требовательнее других фикусов.	Очень яркий рассеянный свет, лучше у южного или восточного окна.	Умеренно, давая почве подсохнуть сверху; не заливайте.	18–24 °C, без сквозняков.	Весной и летом раз в 2 недели.	Не любит перемен места; регулярно протирайте листья, поддерживайте влажность воздуха.
4	Суккулент с мясистыми листьями, часто держат в домашней аптечке.	Яркий свет, допустимо прямое солнце (приучать постепенно).	Редко: после полного просыхания грунта; зимой раз в месяц.	20–28 °C летом; зимой 10–15 °C.	Весной и летом раз в месяц удобрением для кактусов и суккулентов.	Нужен дренаж и рыхлый грунт; от избытка влаги быстро гниёт корень.
5	Ветвистый суккулент, вырастающий в небольшое деревце.	Яркий свет, лучше южное или восточное окно.	Умеренно летом, скудно зимой; грунт должен просохнуть.	18–25 °C; зимой 10–14 °C.	Раз в месяц весной и летом.	Летом полезно выносить на воздух; для здорового роста нужна прохладная зимовка.
6	Очень выносливое растение с жёсткими вертикальными листьями.	От полутени до яркого света; пёстрые формы любят больше света.	Редко: летом раз в 1–2 недели, зимой раз в месяц; не лейте в розетку листьев.	18–28 °C; не ниже 10 °C.	Раз в месяц весной и летом удобрением для суккулентов.	Главная причина гибели — переувлажнение; нужен лёгкий дренированный грунт.
7	Пальмовидное растение с широкими арочными листьями.	Яркий рассеянный свет или полутень.	Умеренно, после подсыхания верхнего слоя; без застоя воды.	18–25 °C; зимой не ниже 12 °C.	Раз в 2–3 недели с весны до осени.	Кончики листьев сохнут от сухого воздуха и жёсткой воды; опрыскивайте и поливайте отстоянной водой.
8	Неприхотливое растение с полосатыми листьями и «детками» на длинных побегах.	Яркий рассеянный свет, переносит полутень.	Регулярно летом, умеренно зимой; запасает влагу в утолщённых корнях.	18–25 °C; не ниже 10 °C.	Раз в 2–3 недели весной и летом.	Кончики листьев буреют от сухого воздуха и жёсткой воды; легко размножается детками.
9	Цветёт белыми покрывалами-соцветиями, любит влагу.	Полутень или рассеянный свет; прямое солнце вредно.	Регулярно, грунт слегка влажный; при пересыхании листья вянут, но быстро оживают.	20–25 °C; не ниже 16 °C.	Раз в 2 недели в период роста и цветения.	Опрыскивайте, используйте мягкую отстоянную воду. При нехватке света не цветёт.
10	Очень выносливое растение, накапливающее воду в клубнях.	Рассеянный свет, переносит тень.	Редко: после полного просыхания грунта, примерно раз в 1–2 недели.	18–26 °C; не ниже 12 °C.	Раз в месяц весной и летом.	Не заливайте: клубни и корни легко гниют. Сок ядовит, работайте в перчатках.
11	Лиана с крупными резными листьями.	Яркий рассеянный свет.	Умеренно, когда верхний слой подсохнет на 3–4 см.	18–27 °C; не ниже 15 °C.	Раз в 2 недели весной и летом.	Нужна опора; воздушные корни не обрезайте, направляйте в грунт. Ядовита при поедании.
12	Неприхотливая лиана с пёстрыми сердцевидными листьями.	Рассеянный свет; в тени пёстрая окраска бледнеет.	Умеренно, после подсыхания верхнего слоя грунта.	18–27 °C; не ниже 12 °C.	Раз в 2–3 недели весной и летом.	Хорош в подвесных кашпо и на опоре; прищипывайте для кустистости. Ядовит для животных.
13	Цветёт почти всё тёплое время года, листья с запахом и тёмным пояском.	Много света, допустимо прямое солнце.	Умеренно, после подсыхания верхнего слоя; без застоя воды.	18–25 °C; зимой лучше 8–12 °C.	Раз в 2 недели удобрением для цветущих растений с калием.	Весной обрезайте и прищипывайте; листья не опрыскивайте.
14	Пеларгония со свисающими побегами и плотными глянцевыми листьями.	Яркий свет, лучше без жаркого полуденного солнца.	Умеренно, без застоя воды.	15–25 °C; зимой 8–12 °C.	Раз в 2 недели в период цветения.	Хороша в подвесных кашпо; удаляйте увядшие соцветия.
15	Суккулент с мясистыми округлыми листьями.	Яркий свет, допустимо прямое солнце.	Редко: после просыхания грунта; зимой раз в месяц.	18–25 °C; зимой 10–15 °C.	Раз в месяц весной и летом удобрением для суккулентов.	Прищипывайте для плотной кроны; в тени вытягивается.
16	Суккулент с яркими соцветиями на зелёных мясистых листьях.	Яркий свет; для цветения нужен короткий световой день, около 10 часов.	Умеренно, зимой редко.	18–25 °C; зимой 12–16 °C.	Раз в 2–3 недели во время роста.	После цветения срезайте соцветия; избегайте переувлажнения.
17	Кустарник с крупными яркими цветами, живущими 1–2 дня.	Яркий свет, немного прямого солнца.	Обильно летом, умеренно зимой; не допускайте пересыхания.	18–25 °C; зимой 12–16 °C.	Раз в 1–2 недели летом, предпочтительны фосфорно-калийные удобрения.	Сбрасывает бутоны при сквозняках и перестановке; формируйте обрезкой весной.
18	Самая распространённая комнатная орхидея; в продаже в основном гибриды.	Яркий рассеянный свет, без прямого солнца.	Погружением горшка на 15–30 минут, когда субстрат высох, а корни посеребрились; обычно раз в 5–10 дней.	18–25 °C; для цветения нужен перепад день/ночь в 5–7 °C.	Раз в 2–3 недели специальным удобрением для орхидей в половинной дозе.	Прозрачный горшок и субстрат из коры; не заливайте точку роста, не срезайте зелёные воздушные корни.
19	Эпифитный кактус с членистыми побегами, цветёт зимой.	Рассеянный свет, без жаркого прямого солнца.	Умеренно; перед бутонизацией полив немного сократите.	18–24 °C; для закладки бутонов осенью 12–16 °C.	Раз в 2 недели весной и летом.	Не переставляйте и не поворачивайте горшок во время бутонизации, иначе растение сбросит бутоны.
20	Небольшое цветущее растение с бархатистыми листьями; в ботанике сейчас относится к роду Streptocarpus.	Яркий рассеянный свет (восточное или западное окно).	Тёплой отстоянной водой через поддон или под корень, не допуская попадания воды на листья.	18–24 °C.	Раз в 2 недели специальным удобрением для фиалок.	Не опрыскивайте, пересаживайте в небольшой горшок; капли воды на листьях на солнце оставляют ожоги.
21	Теплолюбивая овощная культура, одна из самых популярных на дачах.	Полное солнце, не менее 6–8 часов в день.	Редко, но обильно, под корень и без попадания воды на листья.	Оптимум 20–26 °C; рассаду высаживают после окончания заморозков.	Раз в 2–3 недели; в период плодоношения нужны калий и фосфор.	Пасынкуйте и подвязывайте высокие сорта; для профилактики фитофтороза не загущайте посадки и проветривайте теплицу.
22	Главная клубневая культура огорода и полей.	Открытое солнечное место.	Умеренно; особенно важен полив в период бутонизации и цветения.	Сажают при прогреве почвы до 8–10 °C; клубни завязываются при 15–20 °C.	Органика и калий при посадке, окучивание 2 раза за сезон.	Меняйте место посадки каждые 3–4 года; следите за колорадским жуком и фитофторой.
23	Очень теплолюбивая овощная культура.	Полное солнце.	Тёплой водой, обильно и регулярно.	22–28 °C; ниже 15 °C рост останавливается.	Раз в 2 недели комплексным удобрением.	Выращивают рассадой, лучше в теплице; ограничивайте число плодов на кусте.
24	Влаголюбивая теплолюбивая культура, самая популярная на дачах.	Солнечное место или лёгкая полутень.	Часто и обильно тёплой водой, не допускайте пересыхания.	22–28 °C; не переносит заморозков.	Раз в 2 недели: вначале азот, затем калий.	Подвязывайте на шпалеру; регулярный сбор плодов стимулирует новое плодоношение.
25	Неприхотливая и высокоурожайная культура.	Солнечное место.	Обильно, под корень.	18–25 °C; рассаду высаживают после заморозков.	Органика при посадке, подкормка раз в 2–3 недели.	Собирайте молодые плоды длиной 15–20 см; кусту нужно много места, не менее 70×70 см.
26	Теплолюбивая культура, требует много света.	Полное солнце.	Регулярно тёплой водой, не пересушивайте.	22–28 °C; ниже 13 °C рост замедляется.	Раз в 2 недели комплексным удобрением.	Не сажайте рядом сладкий и острый перец, они переопыляются; защитите от ветра.
27	Прохладолюбивая овощная культура.	Солнечное место.	Обильно и регулярно; при нехватке влаги кочаны трескаются.	15–20 °C; лёгкие заморозки переносит.	Вначале азот, затем сбалансированное удобрение.	Следите за капустной белянкой и крестоцветной блошкой; соблюдайте севооборот.
28	Корнеплод, один из базовых овощей огорода.	Солнечное место.	Равномерно; при неравномерном поливе корнеплоды трескаются.	Всходы при 5 °C и выше; рост при 15–20 °C.	Умеренно; свежий навоз вредит (корнеплоды ветвятся).	Нужна рыхлая песчаная почва; прореживайте всходы.
29	Основная луковичная культура огорода.	Солнечное место.	Умеренно; за 3–4 недели до уборки полив прекращают.	Рост при 15–25 °C.	Азот в начале роста, фосфор и калий в середине сезона.	Не сажайте на одном месте чаще чем раз в 3–4 года; убирают, когда перо полегло.
30	Озимый чеснок сажают осенью, яровой весной.	Солнечное место.	Умеренно во время роста; за 2–3 недели до уборки полив прекращают.	Озимый зимует в земле; рост при 12–20 °C.	Весной азот, в начале лета фосфор и калий.	Удаляйте стрелки у стрелкующихся сортов; убирают, когда нижние листья желтеют.
31	Быстрорастущая пряная зелень.	Солнечное место или лёгкая полутень.	Регулярно.	Всходы при 3–5 °C; хорошо растёт при 15–20 °C.	На плодородной почве обычно не нужна.	Сейте несколько раз за сезон с интервалом около 2 недель; не любит пересадку.
32	Самая популярная садовая ягода.	Солнечное место.	Регулярно, лучше капельно и без попадания воды на ягоды.	Зимует под снегом или укрытием; цветёт при 15 °C и выше.	Весной азот, после сбора ягод комплексное удобрение.	Мульчируйте соломой или агроволокном, убирайте лишние усы, обновляйте посадки каждые 3–4 года.
33	Ягодный кустарник с двухлетними побегами.	Солнечное место или лёгкая полутень.	Регулярно, особенно при завязывании и наливе ягод.	Зимостойка; в северных регионах побеги пригибают.	Весной органика или азот, осенью фосфор и калий.	Ежегодно вырезайте отплодоносившие побеги, подвязывайте к шпалере.
34	Зимостойкий ягодный кустарник.	Солнечное место или лёгкая полутень.	Регулярно, особенно при наливе ягод.	Очень зимостойка.	Весной азот, осенью органика и калий.	Проводите омолаживающую обрезку; следите за почковым клещом и мучнистой росой.
35	Основная плодовая культура российских садов.	Солнечное место.	В засуху и при формировании плодов; взрослым деревьям редко, но обильно.	Зимостойкость зависит от сорта.	Весной азот, осенью фосфор, калий и органика.	Проводите весеннюю обрезку и побелку стволов; для опыления нужны разные сорта.
36	Зимостойкое плодовое дерево или куст; многие сорта самобесплодны.	Солнечное место, защищённое от ветра.	В засуху и при наливе ягод.	Зимостойкая культура.	Весной азот, осенью фосфор и калий.	Проводите санитарную обрезку; следите за монилиозом и коккомикозом.
37	Плодовое дерево, часто требует сортов-опылителей.	Солнечное место, защищённое от ветра.	Регулярно в засуху и при наливе плодов.	Зимостойкость зависит от сорта.	Весной азот, осенью фосфор и калий.	Прореживайте завязи, чтобы ветви не ломались под урожаем; обрезайте весной.
38	Самые популярные цветы дачных участков; сорта и гибриды сильно различаются.	Не менее 6 часов солнца в день.	Редко, но обильно, под корень.	В большинстве регионов нужно укрывать на зиму.	Весной органика, летом комплексное удобрение до середины лета.	Обрезайте весной; для профилактики чёрной пятнистости и мучнистой росы обеспечьте проветривание.
39	Луковичное весеннее растение.	Солнечное место.	Умеренно во время роста и цветения.	Луковицы сажают в сентябре–октябре, когда почва остыла до 8–10 °C.	Весной азот и калий.	После цветения срезайте цветонос, листья оставляйте до пожелтения; раз в 2–3 года луковицы выкапывайте и сортируйте.
40	Главная зерновая культура России; бывает озимой и яровой.	Открытое поле.	Чаще богара; критичны периоды выхода в трубку и колошения.	Озимую сеют в конце лета — начале осени, яровую ранней весной; оптимум роста 15–22 °C.	Азот весной в подкормки, фосфор и калий при посеве.	Соблюдайте севооборот; защита от ржавчины, мучнистой росы и фузариоза.
41	Кормовая и пивоваренная зерновая культура, созревает раньше пшеницы.	Открытое поле.	Чаще богара; чувствителен к нехватке влаги при выходе в трубку и колошении.	Яровой сеют рано весной; рост при 15–20 °C.	Азот умеренно (избыток ведёт к полеганию), фосфор и калий при посеве.	Лучшие предшественники — пропашные и бобовые; защита от гельминтоспориозов и ржавчины.
42	Самая зимостойкая зерновая культура, растёт на бедных и кислых почвах.	Открытое поле.	Чаще богара.	Озимую рожь сеют в конце лета — начале осени; хорошо зимует.	Умеренные дозы азота; фосфор и калий при посеве.	Растёт там, где пшеница не удаётся; следите за эрготом (спорыньёй) и полеганием.
43	Влаголюбивая и холодостойкая культура для зерна и корма.	Открытое поле.	Требователен к влаге, особенно при выходе в трубку и метелкованию.	Сеют рано весной; оптимум 15–20 °C.	Азот умеренно, фосфор и калий при посеве.	Хороший фитосанитарный предшественник для других зерновых.
44	Теплолюбивая культура, выращивается на зерно и силос.	Открытое поле, много света.	Особенно важна влага в период выметывания метёлки и налива зерна.	Сев при прогреве почвы до 10–12 °C; оптимум 20–25 °C.	Главный элемент — азот; также фосфор и цинк.	Широкорядный посев, борьба с сорняками на ранних этапах; защита от кукурузного мотылька.
45	Главная масличная культура России, засухоустойчив.	Открытое поле, полное солнце.	Критичный период — от образования корзинки до цветения.	Сев при прогреве почвы до 8–10 °C; оптимум 20–25 °C.	Азот умеренно, фосфор, калий и бор.	Возвращайте на поле не чаще чем через 7–8 лет; болезни — белая гниль, ложная мучнистая роса, заразиха.
46	Тепло- и влаголюбивая бобовая культура, обогащает почву азотом.	Открытое поле.	Критичны периоды цветения и налива бобов.	Сев при прогреве почвы до 12–14 °C; оптимум 20–25 °C.	При инокуляции семян клубеньковыми бактериями азот не нужен; вносят фосфор и калий.	Хороший предшественник для зерновых.
47	Масличная культура, бывает озимой и яровой.	Открытое поле.	Требователен к влаге, особенно при бутонизации и цветении.	Яровой сеют очень рано, озимый в августе; оптимум 15–20 °C.	Высокая потребность в азоте, сере и боре.	Возвращайте на поле не ранее чем через 4 года; защита от крестоцветной блошки и рапсового цветоеда.
48	Двулетнее корнеплодное растение, из сахарной свёклы получают сахар.	Солнечное место.	Равномерно; при засухе падает сахаристость.	Сев при прогреве почвы до 5–7 °C; оптимум 18–22 °C.	Калий и бор; азот умеренно.	Нужна рыхлая плодородная почва с нейтральной реакцией; прореживайте всходы.
49	Теплолюбивая крупяная и медоносная культура.	Открытое поле.	Чувствительна к засухе в период цветения.	Сев при 14–16 °C после окончания заморозков, которые губят всходы.	Умеренные дозы азота; растёт на бедных почвах.	Размещайте вблизи пасек: гречиха хороший медонос.
50	Холодостойкая бобовая культура: зерновая и овощная.	Открытое поле или солнечная грядка.	Требователен к влаге при цветении и наливе бобов.	Сеют очень рано, при 4–6 °C; оптимум 15–20 °C.	Азот не нужен, вносят фосфор и калий.	Высокие сорта подвязывают к опоре; возвращать на то же место стоит не ранее чем через 4–5 лет.
\.


--
-- Data for Name: plants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.plants (plant_id, class_id, name_lat, name_ru, genus_id, category_id, taxon_rank) FROM stdin;
1	Ficus_elastica	Ficus elastica	Фикус каучуконосный (эластика)	1	1	species
2	Ficus_benjamina	Ficus benjamina	Фикус Бенджамина	1	1	species
3	Ficus_lyrata	Ficus lyrata	Фикус лировидный	1	1	species
4	Aloe_vera	Aloe vera	Алоэ вера	2	1	species
5	Aloe_arborescens	Aloe arborescens	Алоэ древовидное (столетник)	2	1	species
6	Dracaena_trifasciata	Dracaena trifasciata	Сансевиерия (щучий хвост, тёщин язык)	3	1	species
7	Dracaena_fragrans	Dracaena fragrans	Драцена душистая	3	1	species
8	Chlorophytum_comosum	Chlorophytum comosum	Хлорофитум хохлатый	9	1	species
9	Spathiphyllum_wallisii	Spathiphyllum wallisii	Спатифиллум («женское счастье»)	10	1	species
10	Zamioculcas_zamiifolia	Zamioculcas zamiifolia	Замиокулькас («долларовое дерево»)	11	1	species
11	Monstera_deliciosa	Monstera deliciosa	Монстера деликатесная	12	1	species
12	Epipremnum_aureum	Epipremnum aureum	Эпипремнум золотистый (потос)	13	1	species
13	Pelargonium_zonale	Pelargonium zonale	Пеларгония зональная (герань)	4	1	species
14	Pelargonium_peltatum	Pelargonium peltatum	Пеларгония плющелистная (ампельная герань)	4	1	species
15	Crassula_ovata	Crassula ovata	Толстянка овальная (денежное дерево)	14	1	species
16	Kalanchoe_blossfeldiana	Kalanchoe blossfeldiana	Каланхоэ Блоссфельда	15	1	species
17	Hibiscus_rosa-sinensis	Hibiscus rosa-sinensis	Гибискус китайский (китайская роза)	16	1	species
18	Phalaenopsis	Phalaenopsis	Фаленопсис (орхидея)	17	1	genus
19	Schlumbergera_truncata	Schlumbergera truncata	Шлюмбергера усечённая (декабрист)	18	1	species
20	Saintpaulia_ionantha	Saintpaulia ionantha	Сенполия (узамбарская фиалка)	19	1	species
21	Solanum_lycopersicum	Solanum lycopersicum	Томат (помидор)	5	2	species
22	Solanum_tuberosum	Solanum tuberosum	Картофель	5	2	species
23	Solanum_melongena	Solanum melongena	Баклажан	5	2	species
24	Cucumis_sativus	Cucumis sativus	Огурец	20	2	species
25	Cucurbita_pepo	Cucurbita pepo	Кабачок (тыква обыкновенная)	21	2	species
26	Capsicum_annuum	Capsicum annuum	Перец овощной	22	2	species
27	Brassica_oleracea	Brassica oleracea	Капуста огородная	8	2	species
28	Daucus_carota	Daucus carota	Морковь	23	2	species
29	Allium_cepa	Allium cepa	Лук репчатый	6	2	species
30	Allium_sativum	Allium sativum	Чеснок	6	2	species
31	Anethum_graveolens	Anethum graveolens	Укроп	24	2	species
32	Fragaria_ananassa	Fragaria × ananassa	Клубника садовая	25	2	species
33	Rubus_idaeus	Rubus idaeus	Малина обыкновенная	26	2	species
34	Ribes_nigrum	Ribes nigrum	Смородина чёрная	27	2	species
35	Malus_domestica	Malus domestica	Яблоня домашняя	28	2	species
36	Prunus_cerasus	Prunus cerasus	Вишня обыкновенная	7	2	species
37	Prunus_domestica	Prunus domestica	Слива домашняя	7	2	species
38	Rosa	Rosa	Роза садовая	29	2	genus
39	Tulipa_gesneriana	Tulipa gesneriana	Тюльпан садовый	30	2	species
40	Triticum_aestivum	Triticum aestivum	Пшеница мягкая	31	3	species
41	Hordeum_vulgare	Hordeum vulgare	Ячмень обыкновенный	32	3	species
42	Secale_cereale	Secale cereale	Рожь посевная	33	3	species
43	Avena_sativa	Avena sativa	Овёс посевной	34	3	species
44	Zea_mays	Zea mays	Кукуруза	35	3	species
45	Helianthus_annuus	Helianthus annuus	Подсолнечник	36	3	species
46	Glycine_max	Glycine max	Соя	37	3	species
47	Brassica_napus	Brassica napus	Рапс	8	3	species
48	Beta_vulgaris	Beta vulgaris	Свёкла (сахарная, столовая, кормовая)	38	3	species
49	Fagopyrum_esculentum	Fagopyrum esculentum	Гречиха посевная	39	3	species
50	Pisum_sativum	Pisum sativum	Горох посевной	40	3	species
\.


--
-- Name: categories_category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.categories_category_id_seq', 3, true);


--
-- Name: genera_genus_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.genera_genus_id_seq', 40, true);


--
-- Name: plants_plant_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('public.plants_plant_id_seq', 50, true);


--
-- Name: categories categories_name_ru_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_name_ru_key UNIQUE (name_ru);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (category_id);


--
-- Name: genera genera_name_lat_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.genera
    ADD CONSTRAINT genera_name_lat_key UNIQUE (name_lat);


--
-- Name: genera genera_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.genera
    ADD CONSTRAINT genera_pkey PRIMARY KEY (genus_id);


--
-- Name: plant_care plant_care_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plant_care
    ADD CONSTRAINT plant_care_pkey PRIMARY KEY (plant_id);


--
-- Name: plants plants_class_id_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plants
    ADD CONSTRAINT plants_class_id_key UNIQUE (class_id);


--
-- Name: plants plants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plants
    ADD CONSTRAINT plants_pkey PRIMARY KEY (plant_id);


--
-- Name: idx_plants_category; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plants_category ON public.plants USING btree (category_id);


--
-- Name: idx_plants_genus; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_plants_genus ON public.plants USING btree (genus_id);


--
-- Name: plant_care plant_care_plant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plant_care
    ADD CONSTRAINT plant_care_plant_id_fkey FOREIGN KEY (plant_id) REFERENCES public.plants(plant_id) ON DELETE CASCADE;


--
-- Name: plants plants_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plants
    ADD CONSTRAINT plants_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(category_id);


--
-- Name: plants plants_genus_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.plants
    ADD CONSTRAINT plants_genus_id_fkey FOREIGN KEY (genus_id) REFERENCES public.genera(genus_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict GN4kMzGwoqgyS4sU13WQBYFnxFC8jsOMzMsPOWSrWF28Jky3DebLJTb1jnxGHJy

