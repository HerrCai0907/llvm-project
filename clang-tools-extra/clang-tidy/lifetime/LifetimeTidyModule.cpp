//===------- HICPPTidyModule.cpp - clang-tidy -----------------------------===//
//
// Part of the LLVM Project, under the Apache License v2.0 with LLVM Exceptions.
// See https://llvm.org/LICENSE.txt for license information.
// SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception
//
//===----------------------------------------------------------------------===//

#include "../ClangTidy.h"
#include "../ClangTidyModule.h"
#include "../ClangTidyModuleRegistry.h"
#include "UseCaptureByCheck.h"

namespace clang::tidy {
namespace lifetime {

class LifeTimeModule : public ClangTidyModule {
public:
  void addCheckFactories(ClangTidyCheckFactories &CheckFactories) override {
    CheckFactories.registerCheck<UseCaptureByCheck>("lifetime-use-capture-by");
  }
};

// Register the HICPPModule using this statically initialized variable.
static ClangTidyModuleRegistry::Add<LifeTimeModule>
    X("hicpp-module", "Adds High-Integrity C++ checks.");

} // namespace lifetime

// This anchor is used to force the linker to link in the generated object file
// and thus register the HICPPModule.
volatile int LifetimeModuleAnchorSource =
    0; // NOLINT(misc-use-internal-linkage)

} // namespace clang::tidy
