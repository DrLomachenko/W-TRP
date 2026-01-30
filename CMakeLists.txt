cmake_minimum_required(VERSION 3.10)

# Собираем строго под arm64 (Apple Silicon), чтобы совпадало с libhighs.dylib
set(CMAKE_OSX_ARCHITECTURES "arm64" CACHE STRING "" FORCE)

project(WeightTRP)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Релизные флаги (CLion в Release-профиле их подхватит)
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -DNDEBUG")
set(CMAKE_C_FLAGS_RELEASE "-O3 -DNDEBUG")

# --- HiGHS через pkg-config ---
find_package(PkgConfig REQUIRED)
pkg_check_modules(HIGHS REQUIRED highs)

# Все исходники
set(SOURCES
        src/main.cpp
        src/DAG.cpp
        src/Instance.cpp
        src/BuilderPF.cpp
        src/BuilderLC.cpp
        src/BuilderLSG.cpp
        src/KTNSSolver.cpp
        src/HighsLPSolver.cpp
        src/HighsFlowSolver.cpp
        src/DAG_Solver.cpp
        src/HighsMCFSolver.cpp
        src/Mecler/CommandLine.cpp
        src/Mecler/Genetic.cpp
        src/Mecler/Individual.cpp
        src/Mecler/LocalSearch.cpp
        src/Mecler/Parameters.cpp
        src/Mecler/Population.cpp
        )

add_executable(WeightTRP ${SOURCES})

# Инклуды и библиотеки HiGHS
target_include_directories(WeightTRP PRIVATE ${HIGHS_INCLUDE_DIRS})
target_link_directories(WeightTRP PRIVATE ${HIGHS_LIBRARY_DIRS})
target_link_libraries(WeightTRP PRIVATE ${HIGHS_LIBRARIES})
