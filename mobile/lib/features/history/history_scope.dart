import 'dart:async';

import 'package:flutter/material.dart';

import 'data/history_repository.dart';

class HistoryScope extends StatefulWidget {
  const HistoryScope({
    super.key,
    required this.repository,
    required this.child,
  });

  final HistoryRepository repository;
  final Widget child;

  static HistoryRepository? maybeOf(BuildContext context) => context
      .dependOnInheritedWidgetOfExactType<_HistoryInherited>()
      ?.repository;

  @override
  State<HistoryScope> createState() => _HistoryScopeState();
}

class _HistoryScopeState extends State<HistoryScope>
    with WidgetsBindingObserver {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      unawaited(widget.repository.runMaintenance());
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) =>
      _HistoryInherited(repository: widget.repository, child: widget.child);
}

class _HistoryInherited extends InheritedNotifier<HistoryRepository> {
  const _HistoryInherited({required this.repository, required super.child})
    : super(notifier: repository);

  final HistoryRepository repository;
}
