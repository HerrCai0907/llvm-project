set(LLVM_LINK_COMPONENTS
  Support
)

add_clang_library(clangTidyLifetimeModule STATIC
  LifetimeTidyModule.cpp
  UseCaptureByCheck.cpp

  LINK_LIBS
  clangTidy
  clangTidyUtils

  DEPENDS
  omp_gen
  ClangDriverOptions
)

clang_target_link_libraries(clangTidyLifetimeModule
  PRIVATE
  clangAST
  clangASTMatchers
  clangBasic
  clangLex
  clangSerialization
)
